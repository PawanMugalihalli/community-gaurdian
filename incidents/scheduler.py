import logging
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings

logger = logging.getLogger(__name__)

_scheduler = None


def start_scheduler():
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.info("Scheduler already running.")
        return _scheduler

    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception as exc:
            logger.warning("Unable to shut down previous scheduler cleanly: %s", exc)

    _scheduler = BackgroundScheduler(
        job_defaults={"coalesce": True, "max_instances": 1},
        executors={"default": ThreadPoolExecutor(5)},
    )

    _scheduler.add_job(
        ingest_rss,
        trigger=IntervalTrigger(minutes=30),
        id="rss_ingestion",
        name="Fetch RSS incidents",
        replace_existing=True,
        misfire_grace_time=300,
    )
    _scheduler.add_job(
        enrich_incidents,
        trigger=IntervalTrigger(minutes=settings.BATCH_INTERVAL_MINUTES),
        id="enrich_incidents",
        name="Enrich pending incidents",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started. "
        f"Enrichment job runs every {settings.BATCH_INTERVAL_MINUTES} minutes."
    )
    return _scheduler


def ingest_rss():
    logger.info("RSS ingestion triggered")

    try:
        from incidents.services.rss_service import RSSService

        RSSService.fetch_all_cities()
    except Exception as exc:
        logger.error("RSS ingestion failed: %s", exc)


def enrich_incidents():
    logger.info("Enrichment job triggered.")
    try:
        from incidents.services.enrichment_service import EnrichmentService

        EnrichmentService.enrich_pending()
    except Exception as exc:
        logger.error("Enrichment job failed: %s", exc)
   