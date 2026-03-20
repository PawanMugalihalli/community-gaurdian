import logging

from incidents.models import DigestLog


logger = logging.getLogger(__name__)


class DigestService:

    @staticmethod
    def log_digest(profile, incidents: list) -> None:
        try:
            DigestLog.objects.create(
                user=profile,
                ai_used=any(i.ai_enriched for i in incidents),
                result_json={
                    'total': len(incidents),
                    'incident_ids': [i.id for i in incidents],
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log digest for profile {profile.id}: {e}")
