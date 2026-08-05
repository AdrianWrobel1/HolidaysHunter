import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.database.session import async_session_factory
from app.models.enums import Provider
from app.providers.registry import get_all_providers
from app.services.import_service import run_import

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_provider_import(provider: Provider) -> None:
    """Job function executed by the scheduler for each provider.

    Creates its own database session so each import is independent.
    Errors are caught and logged — one failing provider cannot block others.
    """
    logger.info("Scheduler: starting import for %s", provider.value)
    try:
        async with async_session_factory() as session:
            await run_import(provider, session)
            await session.commit()
    except Exception:
        logger.exception("Scheduler: import failed for %s", provider.value)


def configure_scheduler() -> None:
    """Register import jobs for all registered providers.

    Each provider gets its own independent job so they can run on
    different schedules and failures are isolated.
    """
    providers = get_all_providers()

    for provider in providers:
        scheduler.add_job(
            _run_provider_import,
            trigger="interval",
            minutes=settings.import_interval_minutes,
            args=[provider],
            id=f"import_{provider.value}",
            name=f"Import {provider.value}",
            replace_existing=True,
        )
        logger.info(
            "Scheduler: registered %s import every %d minutes",
            provider.value,
            settings.import_interval_minutes,
        )


def start_scheduler() -> None:
    configure_scheduler()
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
