"""Health endpoint.

Endpoints are declared with ``def``, not ``async def``: the Oracle driver is
synchronous, so FastAPI runs these in a threadpool and the event loop stays free.
"""

from fastapi import APIRouter, Depends, Response, status

from ..db import Database
from ..dependencies import get_database
from ..repositories.health import HealthRepository
from ..schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness and database connectivity",
    responses={
        status.HTTP_200_OK: {"description": "The database answered."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The process is up but the database did not answer.",
            "model": HealthResponse,
        },
    },
)
def health(
    response: Response,
    database: Database = Depends(get_database),
) -> HealthResponse:
    """Report 503 when the database cannot be reached.

    Returning 200 regardless would make this useless to the compose healthcheck and
    to whatever fronts the application in production.
    """
    if not HealthRepository(database).ping():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded", database="unreachable")
    return HealthResponse(status="ok", database="ok")
