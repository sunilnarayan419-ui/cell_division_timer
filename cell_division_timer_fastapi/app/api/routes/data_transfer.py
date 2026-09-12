"""Data transfer endpoints for CSV dataset export and batch instrument import."""

from fastapi import APIRouter, File, Response, UploadFile, status
from app.api.deps import CSVServiceDep
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get(
    "/export/csv",
    summary="Export Division Dataset to CSV",
    description="Streams all division records with biological metadata as a downloadable CSV file for external analysis (e.g. R, Python, Excel).",
)
def export_csv(
    service: CSVServiceDep,
) -> Response:
    """Download full division kinetics dataset as CSV."""
    csv_data = service.export_divisions_to_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="cell_division_dataset.csv"'
        },
    )


@router.post(
    "/import/csv",
    summary="Batch Import Division Records from CSV",
    description="Uploads a CSV of cell division observations. Missing parent cell lines are automatically registered.",
    status_code=status.HTTP_200_OK,
)
async def import_csv(
    service: CSVServiceDep,
    file: UploadFile = File(..., description="CSV file containing division records"),
) -> dict:
    """Upload and parse CSV dataset of cell divisions."""
    content_bytes = await file.read()
    csv_text = content_bytes.decode("utf-8")
    result = service.import_divisions_from_csv(csv_text)
    return result
