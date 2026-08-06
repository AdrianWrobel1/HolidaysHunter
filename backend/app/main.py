import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.alerts import router as alerts_router
from app.api.health import router as health_router
from app.api.offers import router as offers_router
from app.api.profiles import router as profiles_router
from app.api.qa import router as qa_router
from app.api.workspace import router as workspace_router
from app.notifications.telegram_bot import telegram_bot_listener
from app.scheduler.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — starts scheduler and telegram bot on startup, stops on shutdown."""
    logger.info("HolidaysHunter backend starting")
    from app.database.base import Base
    from app.database.session import engine
    import app.models  # Ensure all models are loaded

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logger.warning("Database schema creation on startup skipped or failed: %s", exc)

    start_scheduler()
    await telegram_bot_listener.start()
    yield
    await telegram_bot_listener.stop()
    stop_scheduler()
    logger.info("HolidaysHunter backend stopped")


app = FastAPI(
    title="HolidaysHunter",
    description="Private travel monitoring platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(offers_router)
app.include_router(profiles_router)
app.include_router(alerts_router)
app.include_router(qa_router)
app.include_router(admin_router)
app.include_router(workspace_router)



