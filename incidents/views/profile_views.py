from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from incidents.serializers import UserSerializer
from incidents.services.profile_service import UserProfileService
from incidents.views.api_exceptions import handle_exceptions


class UserProfileViewSet(ViewSet):

    @handle_exceptions
    def create(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = UserProfileService.create(serializer.validated_data)
        return Response(
            UserSerializer(profile).data,
            status=status.HTTP_201_CREATED,
        )

    @handle_exceptions
    def retrieve(self, request, pk=None):
        profile = UserProfileService.get_by_id(pk)
        return Response(
            UserSerializer(profile).data,
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def partial_update(self, request, pk=None):
        profile = UserProfileService.update(pk, request.data)
        return Response(
            UserSerializer(profile).data,
            status=status.HTTP_200_OK,
        )
