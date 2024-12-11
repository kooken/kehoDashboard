from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apps import MainConfig
from .views import TelemetryViewSet, dashboard, user_details

app_name = MainConfig.name

router = DefaultRouter()
router.register(r'telemetry', TelemetryViewSet, basename='telemetry')

urlpatterns = [
    path('api/', include(router.urls)),

    path('', dashboard, name='dashboard'),
    path('user/<int:user_id>/', user_details, name='user_details'),
]