import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings


logger = logging.getLogger(__name__)


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        enrich_incidents,
        trigger=IntervalTrigger(minutes=settings.BATCH_INTERVAL_MINUTES),
        id='enrich_incidents',
        name='Enrich pending incidents',
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. "
        f"Enrichment job runs every {settings.BATCH_INTERVAL_MINUTES} minutes."
    )


def enrich_incidents():
    logger.info("Enrichment job triggered.")
    try:
        from incidents.services.enrichment_service import EnrichmentService
        EnrichmentService.enrich_pending()
    except Exception as e:
        logger.error(f"Enrichment job failed: {e}")