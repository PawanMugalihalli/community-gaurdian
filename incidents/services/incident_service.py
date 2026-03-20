import logging
from incidents.models import Incident


logger = logging.getLogger(__name__)


class IncidentService:

    @staticmethod
    def create(data: dict) -> Incident:
        return Incident.objects.create(**data)

    @staticmethod
    def get_by_id(incident_id: int) -> Incident:
        try:
            return Incident.objects.get(id=incident_id)
        except Incident.DoesNotExist:
            raise ValueError(f"Incident with id {incident_id} does not exist.")

    @staticmethod
    def update(incident_id: int, data: dict) -> Incident:
        try:
            incident = Incident.objects.get(id=incident_id)
        except Incident.DoesNotExist:
            raise ValueError(f"Incident with id {incident_id} does not exist.")

        allowed_fields = {'title', 'description', 'location', 'source'}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(incident, field, value)

        incident.save()
        return incident

    @staticmethod
    def get_unenriched():
        return Incident.objects.filter(ai_enriched=False)

    @staticmethod
    def get_incidents(
        location=None,
        category=None,
        severity=None,
        search=None,
        concerns=None,
    ):
        qs = Incident.objects.filter(is_noise=False)
        qs = IncidentService._apply_location(qs, location)
        qs = IncidentService._apply_category(qs, category, concerns)
        qs = IncidentService._apply_severity(qs, severity)
        qs = IncidentService._apply_search(qs, search)
        return qs.order_by('-severity', '-created_at')

    @staticmethod
    def _apply_location(qs, location):
        return qs.filter(location__icontains=location) if location else qs

    @staticmethod
    def _apply_category(qs, category, concerns):
        if category:
            return qs.filter(category=category)
        if concerns:
            return qs.filter(category__in=concerns)
        return qs

    @staticmethod
    def _apply_severity(qs, severity):
        if severity is None:
            return qs
        # UI: 3+ / 4+ = minimum severity; 5 = exactly 5
        if severity >= 5:
            return qs.filter(severity=5)
        return qs.filter(severity__gte=severity)

    @staticmethod
    def _apply_search(qs, search):
        if search:
            return qs.filter(title__icontains=search) | \
                   qs.filter(description__icontains=search)
        return qs