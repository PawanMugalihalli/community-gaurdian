"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from incidents.ui_views import feed_view, profile_view, report_view
from incidents.auth_views import signup_view, login_view, logout_view

urlpatterns = [
    path('admin/',   admin.site.urls),
    path('api/',     include('incidents.urls')),
    path('incidents/', feed_view, name='feed'),
    path('', RedirectView.as_view(pattern_name='feed', permanent=False)),
    path('profile/', profile_view, name='profile'),
    path('report/',  report_view,  name='report'),
    path('login/',   login_view,   name='login'),
    path('signup/',  signup_view,  name='signup'),
    path('logout/',  logout_view,  name='logout'),
]
