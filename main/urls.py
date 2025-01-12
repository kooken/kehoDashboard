from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apps import MainConfig
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from .views import dashboard, user_details, login_view, ClientDataView, TelemetryDataViewSet

app_name = MainConfig.name

router = DefaultRouter()
router.register(r'telemetry', TelemetryDataViewSet, basename='telemetry')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('user/<int:user_id>/', user_details, name='user_details'),
    path('data/', TemplateView.as_view(template_name='main/client_data.html'), name='client_data'),
    path('api/data/', csrf_exempt(ClientDataView.as_view()), name='api_client_data'),
]
