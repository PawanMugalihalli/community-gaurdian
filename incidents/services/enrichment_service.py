import logging
from django.conf import settings
from incidents.models import Incident
from incidents.services.groq_service import GroqService
from incidents.services.fallback_service import FallbackService


logger = logging.getLogger(__name__)


class EnrichmentService:

    @staticmethod
    def enrich_pending() -> None:
        pending = Incident.objects.filter(ai_enriched=False)

        if not pending.exists():
            logger.info("No pending incidents to enrich.")
            return

        logger.info(f"Found {pending.count()} pending incidents to enrich.")

        chunk_size = settings.BATCH_CHUNK_SIZE
        pending_list = list(pending)

        chunks = [
            pending_list[i:i + chunk_size]
            for i in range(0, len(pending_list), chunk_size)
        ]

        logger.info(f"Processing {len(chunks)} chunk(s) of size {chunk_size}.")

        for index, chunk in enumerate(chunks):
            EnrichmentService._process_chunk(chunk, index + 1, len(chunks))

    @staticmethod
    def _process_chunk(chunk: list, chunk_number: int, total_chunks: int) -> None:
        logger.info(
            f"Processing chunk {chunk_number}/{total_chunks} "
            f"with {len(chunk)} incidents."
        )

        try:
            result = GroqService.analyze(chunk)
            ai_used = True
            logger.info(f"Chunk {chunk_number} enriched by AI.")
        except Exception as e:
            logger.warning(
                f"AI failed for chunk {chunk_number}: {e}. "
                f"Running fallback."
            )
            result = FallbackService.analyze(chunk)
            ai_used = False

        EnrichmentService._save_results(chunk, result, ai_used)

    @staticmethod
    def _save_results(chunk: list, result: dict, ai_used: bool) -> None:
        result_map = {item['id']: item for item in result['results']}

        for incident in chunk:
            enriched = result_map.get(incident.id)

            if not enriched:
                logger.warning(
                    f"No enrichment result found for incident {incident.id}. "
                    f"Skipping."
                )
                continue

            incident.is_noise     = enriched['is_noise']
            incident.category     = enriched.get('category', '')
            incident.severity     = enriched.get('severity') or 1
            incident.action_steps = enriched.get('action_steps', '')
            incident.is_enriched  = True
            incident.ai_enriched  = ai_used

            incident.save()

        logger.info(
            f"Saved enrichment results for {len(chunk)} incidents. "
            f"AI used: {ai_used}."
        )