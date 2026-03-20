import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from incidents.serializers import IncidentSerializer
from incidents.services.incident_service import IncidentService
from incidents.services.profile_service import UserProfileService
from incidents.views.digest_service import DigestService


logger = logging.getLogger(__name__)


class IncidentViewSet(ViewSet):

    def list(self, request):
        profile_id = request.query_params.get('profile_id')
        location   = request.query_params.get('location')
        category   = request.query_params.get('category')
        severity   = request.query_params.get('severity')
        search     = request.query_params.get('search')

        try:
            profile  = self._resolve_profile(profile_id)
            location = self._resolve_location(location, profile)
            concerns = self._resolve_concerns(category, profile)

            incidents = IncidentService.get_incidents(
                location=location,
                category=category,
                severity=int(severity) if severity else None,
                search=search,
                concerns=concerns,
            )

            self._log_if_profile(profile, incidents)

            serializer = IncidentSerializer(incidents, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error listing incidents: {e}")
            return Response(
                {'error': 'Failed to retrieve incidents.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request):
        serializer = IncidentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            incident = IncidentService.create(serializer.validated_data)
            return Response(
                IncidentSerializer(incident).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            return Response(
                {'error': 'Failed to create incident.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request, pk=None):
        try:
            incident = IncidentService.get_by_id(pk)
            return Response(
                IncidentSerializer(incident).data,
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error retrieving incident {pk}: {e}")
            return Response(
                {'error': 'Failed to retrieve incident.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None):
        try:
            incident = IncidentService.update(pk, request.data)
            return Response(
                IncidentSerializer(incident).data,
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error updating incident {pk}: {e}")
            return Response(
                {'error': 'Failed to update incident.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _resolve_profile(self, profile_id):
        return UserProfileService.get_by_id(profile_id) if profile_id else None

    def _resolve_location(self, location, profile):
        return location or (profile.location if profile else None)

    def _resolve_concerns(self, category, profile):
        if category or not profile:
            return None
        return profile.concerns if profile.concerns else None

    def _log_if_profile(self, profile, incidents):
        if profile:
            DigestService.log_digest(profile, list(incidents))