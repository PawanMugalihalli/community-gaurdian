import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from incidents.serializers import UserSerializer
from incidents.services.profile_service import UserProfileService


logger = logging.getLogger(__name__)


class UserProfileViewSet(ViewSet):

    def create(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = UserProfileService.create(serializer.validated_data)
            return Response(
                UserSerializer(profile).data,
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            return Response(
                {'error': 'Failed to create profile.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request, pk=None):
        try:
            profile = UserProfileService.get_by_id(pk)
            return Response(
                UserSerializer(profile).data,
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error retrieving profile {pk}: {e}")
            return Response(
                {'error': 'Failed to retrieve profile.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None):
        try:
            profile = UserProfileService.update(pk, request.data)
            return Response(
                UserSerializer(profile).data,
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Error updating profile {pk}: {e}")
            return Response(
                {'error': 'Failed to update profile.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )