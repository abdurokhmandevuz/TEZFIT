from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('api/dashboard', views.api_dashboard, name='api_dashboard'),
    path('api/profile', views.api_profile, name='api_profile'),
    path('api/scan-photo', views.api_scan_photo, name='api_scan_photo'),
    path('api/scan-text', views.api_scan_text, name='api_scan_text'),
    path('api/save-meal', views.api_save_meal, name='api_save_meal'),
    path('api/goals', views.api_goals, name='api_goals'),
    path('api/reset-user', views.api_reset_user, name='api_reset_user'),
    path('', admin.site.urls),
]
