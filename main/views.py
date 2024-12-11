from django.shortcuts import render, get_object_or_404
import folium
from rest_framework.response import Response
from .models import User
from rest_framework import viewsets
from .serializers import TelemetrySerializer


def dashboard(request):
    users = User.objects.all()
    return render(request, 'main/dashboard.html', {'users': users})


def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    telemetry = user.telemetry.all()

    coordinates = [
        {
            "latitude": data.latitude,
            "longitude": data.longitude,
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ambient_temperature": data.ambient_temperature,
            "target_temperature": data.thermostat_target_temperature,
            "current_temperature": data.thermostat_current_temperature,
        }
        for data in telemetry
    ]

    if telemetry.exists():
        initial_location = [telemetry.first().latitude, telemetry.first().longitude]
    else:
        initial_location = [0, 0]

    map_folium = folium.Map(location=initial_location, zoom_start=13)

    points = []
    for i, data in enumerate(telemetry):
        folium.CircleMarker(
            location=[data.latitude, data.longitude],
            radius=6,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.7,
            popup=f"<strong>Time:</strong> {data.timestamp}<br>"
                  f"<strong>Ambient Temp:</strong> {data.ambient_temperature}°C<br>"
                  f"<strong>Target Temp:</strong> {data.thermostat_target_temperature}°C<br>"
                  f"<strong>Current Temp:</strong> {data.thermostat_current_temperature}°C"
        ).add_to(map_folium)

        points.append([data.latitude, data.longitude])

    if len(points) > 1:
        folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(map_folium)

    map_html = map_folium._repr_html_()

    return render(request, 'main/user_details.html', {
        'user': user,
        'telemetry': telemetry,
        'map_html': map_html,
        'coordinates': coordinates,
    })


class TelemetryViewSet(viewsets.ViewSet):
    def create(self, request):
        email = request.data.get('email')
        user, _ = User.objects.get_or_create(email=email)

        telemetry_data = {
            'user': user.id,
            'latitude': request.data.get('latitude'),
            'longitude': request.data.get('longitude'),
            'ambient_temperature': request.data.get('ambient_temperature'),
            'thermostat_target_temperature': request.data.get('thermostat_target_temperature'),
            'thermostat_current_temperature': request.data.get('thermostat_current_temperature'),
        }

        serializer = TelemetrySerializer(data=telemetry_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "success", "data": serializer.data})
