from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apps import MainConfig
from .views import TelemetryDataSerializer, dashboard, user_details, login_view, ClientDataView

app_name = MainConfig.name

router = DefaultRouter()
router.register(r'telemetry', TelemetryDataSerializer, basename='telemetry')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('user/<int:user_id>/', user_details, name='user_details'),
    path('data/', ClientDataView.as_view(), name='client_data'),

]
