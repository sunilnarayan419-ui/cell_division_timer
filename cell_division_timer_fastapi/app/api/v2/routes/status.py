"""v2 beta lifecycle status and migration roadmap."""

from fastapi import APIRouter
from app.api.v2.schemas import V2BetaStatusResponse

router = APIRouter(tags=["v2 Beta Lifecycle"])


@router.get("/status", response_model=V2BetaStatusResponse, summary="Get v2 Beta Status and Changelog")
def get_v2_status() -> V2BetaStatusResponse:
    """Retrieve v2 beta lifecycle stage, active capabilities, and migration roadmap."""
    return V2BetaStatusResponse(
        version="2.0.0-beta.1",
        status="beta",
        deprecation_notice=None,
        lifecycle="active-development",
        features=[
            "Mitotic sub-phase temporal breakdown (Prophase, Metaphase, Anaphase, Telophase)",
            "High-throughput batch kinetic analysis with parallel processing",
            "Arrhenius Q10 temperature coefficient and activation energy (Ea) modeling",
            "Spindle Assembly Checkpoint (SAC) delay index and arrest probability scoring",
            "Full header-based and path-based version negotiation via APIVersioningMiddleware",
        ],
        backward_compatibility={
            "v1_supported": True,
            "v1_deprecated": False,
            "v1_sunset_date": None,
            "breaking_changes": "v2 maintains backward-compatible schema field aliases while introducing richer kinetic telemetry.",
        },
        changelog=[
            "2026-Q1: Introduced v2-beta API architecture and ASGI versioning middleware",
            "2026-Q1: Added POST /api/v2/divisions/batch-analyze for bulk kinetic profiling",
            "2026-Q1: Added GET /api/v2/analytics/predictive-kinetics for Arrhenius thermal analysis",
            "2026-Q1: Added MitoticSubphaseTiming schema with SAC arrest probability",
        ],
    )
