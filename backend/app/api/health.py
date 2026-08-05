from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database.session import engine

router = APIRouter(tags=["health"])


async def check_database_connection() -> bool:
    """Verify the application can reach PostgreSQL and the main offers table exists."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1 FROM offers LIMIT 1"))
        return True
    except Exception:
        return False


@router.get("/health")
async def health_check() -> JSONResponse:
    database_ok = await check_database_connection()
    payload = {
        "status": "ok" if database_ok else "degraded",
        "database": "ok" if database_ok else "unavailable",
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )
