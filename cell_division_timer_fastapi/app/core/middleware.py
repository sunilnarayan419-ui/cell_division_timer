"""API versioning and header-based routing middleware."""

import json
import re
from typing import Optional, Set
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from app.core.logging import logger

V1_ALIAS = "v1"
V2_BETA_ALIAS = "v2-beta"

SUPPORTED_VERSIONS: Set[str] = {V1_ALIAS, V2_BETA_ALIAS}
VERSION_HEADER_NAMES = ("x-api-version", "accept-version")

# Regular expression to extract version from vendor Accept header (e.g. application/vnd.celldivision.v2+json)
VENDOR_MIME_REGEX = re.compile(
    r"application/vnd\.(?:celldivision|celltimer)\.v(?P<ver>[12](?:\.0)?(?:-beta)?)\+json",
    re.IGNORECASE,
)


def normalize_version(raw_val: Optional[str]) -> Optional[str]:
    """Normalize user-provided version string into canonical representation ('v1' or 'v2-beta').

    Returns None if the raw string cannot be resolved to a supported version.
    """
    if not raw_val:
        return None
    val = raw_val.strip().lower()
    if val in ("1", "v1", "1.0", "v1.0"):
        return V1_ALIAS
    if val in ("2", "v2", "2.0", "v2.0", "2-beta", "v2-beta", "beta"):
        return V2_BETA_ALIAS
    return None


class APIVersioningMiddleware:
    """ASGI Middleware providing dynamic API version negotiation and header-based routing.

    Features:
    1. Distinguishes between v1 (Stable Production) and v2-beta (Beta Evolution).
    2. Supports explicit path-based routing: `/api/v1/...` and `/api/v2/...`.
    3. Supports header-based routing for unversioned `/api/...` endpoints:
       - Header: `X-API-Version: 2` or `Accept-Version: 2`
       - Vendor MIME: `Accept: application/vnd.celldivision.v2+json`
       - Query parameter: `?api-version=2`
    4. Automatically adds lifecycle transparency headers:
       - `X-API-Version`: canonical version (e.g. `v1`, `v2-beta`)
       - `X-API-Lifecycle`: `stable` or `beta`
       - `Vary`: `X-API-Version, Accept`
    5. Rejects unsupported version requests with structured 400 Bad Request and version directory.
    """

    def __init__(self, app: ASGIApp, default_version: str = V1_ALIAS):
        self.app = app
        self.default_version = default_version

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        headers = Headers(raw=scope.get("headers", []))

        # Extract version from headers or query string
        raw_header_version: Optional[str] = None
        for h_name in VERSION_HEADER_NAMES:
            if h_name in headers:
                raw_header_version = headers[h_name]
                break

        # Check vendor accept header if not found in explicit version headers
        if not raw_header_version and "accept" in headers:
            match = VENDOR_MIME_REGEX.search(headers["accept"])
            if match:
                raw_header_version = match.group("ver")

        # Check query string (?api-version=... or ?version=...)
        if not raw_header_version:
            query_string = scope.get("query_string", b"").decode("utf-8")
            for param in query_string.split("&"):
                if "=" in param:
                    k, v = param.split("=", 1)
                    if k.lower() in ("api-version", "version", "v"):
                        raw_header_version = v
                        break

        # Validate requested version if client provided one
        canonical_requested_version: Optional[str] = None
        if raw_header_version is not None:
            canonical_requested_version = normalize_version(raw_header_version)
            if canonical_requested_version is None:
                # Unsupported version requested
                logger.warning(f"Rejected unsupported API version: '{raw_header_version}' on {path}")
                error_body = json.dumps(
                    {
                        "detail": (
                            f"Unsupported API version '{raw_header_version}'. "
                            f"Supported versions: {', '.join(sorted(SUPPORTED_VERSIONS))}."
                        ),
                        "code": "UNSUPPORTED_API_VERSION",
                        "requested_version": raw_header_version,
                        "supported_versions": sorted(list(SUPPORTED_VERSIONS)),
                        "default_version": self.default_version,
                    }
                ).encode("utf-8")

                await send(
                    {
                        "type": "http.response.start",
                        "status": 400,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(error_body)).encode("ascii")),
                            (b"x-api-supported-versions", b"v1, v2-beta"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": error_body})
                return

        # Determine target version and path resolution
        resolved_version = self.default_version
        resolved_lifecycle = "stable"

        if path.startswith("/api/v1/"):
            resolved_version = V1_ALIAS
            resolved_lifecycle = "stable"
        elif path.startswith("/api/v2/"):
            resolved_version = V2_BETA_ALIAS
            resolved_lifecycle = "beta"
        elif path.startswith("/api/") and not path.startswith("/api/v"):
            # Unversioned path (e.g. /api/divisions, /api/cells, /api/analytics)
            # Route based on header negotiation or fallback to default v1
            target_version = canonical_requested_version or self.default_version
            target_prefix = "/api/v1" if target_version == V1_ALIAS else "/api/v2"
            suffix = path[4:]  # Suffix after /api
            rewritten_path = target_prefix + suffix

            logger.debug(
                f"Rewriting unversioned request '{path}' -> '{rewritten_path}' "
                f"(target_version={target_version})"
            )
            scope["path"] = rewritten_path
            resolved_version = target_version
            resolved_lifecycle = "beta" if target_version == V2_BETA_ALIAS else "stable"

        # Intercept response to inject versioning & lifecycle headers
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))

                # Inject X-API-Version
                raw_headers.append((b"x-api-version", resolved_version.encode("ascii")))
                # Inject X-API-Lifecycle (stable vs beta)
                raw_headers.append((b"x-api-lifecycle", resolved_lifecycle.encode("ascii")))
                # Inject Vary header for caching intermediaries
                raw_headers.append((b"vary", b"X-API-Version, Accept"))

                if resolved_lifecycle == "beta":
                    raw_headers.append(
                        (
                            b"x-api-warning",
                            b'299 - "v2-beta is an active preview and subject to experimental evolution."',
                        )
                    )

                message["headers"] = raw_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)
