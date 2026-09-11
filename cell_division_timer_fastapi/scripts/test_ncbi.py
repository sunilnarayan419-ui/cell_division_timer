"""Manual integration test for NCBI E-utilities."""

import asyncio
import sys
from pathlib import Path

# Allow imports from the project root when running:
# python scripts/test_ncbi.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.services.ncbi_service import NCBIService


async def main() -> None:
    """Test NCBI PubMed search."""

    settings = get_settings()

    print("=" * 60)
    print("NCBI E-UTILITIES CONNECTION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Check configuration
    # --------------------------------------------------------

    print("\n[1] Checking configuration...")

    if not settings.NCBI_API_KEY:
        print("❌ NCBI_API_KEY is missing.")
        print("   Add it to your .env file.")
        return

    if not settings.NCBI_EMAIL:
        print("⚠️  NCBI_EMAIL is empty.")

    print("✅ NCBI API key found")
    print(f"   Tool:  {settings.NCBI_TOOL}")
    print(f"   Email: {settings.NCBI_EMAIL}")

    # Never print the actual API key.
    masked_key = (
        settings.NCBI_API_KEY[:4]
        + "..."
        + settings.NCBI_API_KEY[-4:]
    )

    print(f"   Key:   {masked_key}")

    # --------------------------------------------------------
    # 2. Initialize service
    # --------------------------------------------------------

    print("\n[2] Initializing NCBI service...")

    service = NCBIService()

    print("✅ NCBIService initialized")

    # --------------------------------------------------------
    # 3. Search PubMed
    # --------------------------------------------------------

    query = "HeLa cell cycle"

    print(f"\n[3] Searching PubMed...")
    print(f"    Query: {query}")

    try:
        result = await service.search_pubmed(
            query=query,
            retmax=5,
        )

    except Exception as exc:
        print("\n❌ NCBI request failed.")
        print(f"   Error: {exc}")
        return

    # --------------------------------------------------------
    # 4. Inspect response
    # --------------------------------------------------------

    search_result = result.get("esearchresult", {})

    count = search_result.get("count", "0")
    pmids = search_result.get("idlist", [])

    print("\n[4] PubMed response received")

    print(f"    Total matching records: {count}")
    print(f"    PMIDs returned: {len(pmids)}")

    if not pmids:
        print("\n⚠️  No PubMed records found.")
        return

    print("\n    PMIDs:")

    for pmid in pmids:
        print(f"    - {pmid}")

    print("\n" + "=" * 60)
    print("✅ NCBI E-UTILITIES TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())