from django.urls import path, include
from rest_framework.routers import DefaultRouter

from incidents.views.incident_views import IncidentViewSet
from incidents.views.profile_views import UserProfileViewSet


router = DefaultRouter()
router.register(r'incidents', IncidentViewSet, basename='incidents')
router.register(r'profiles', UserProfileViewSet, basename='profiles')

urlpatterns = [
    path('', include(router.urls)),
]