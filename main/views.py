from django.shortcuts import render, get_object_or_404, redirect
import folium
from rest_framework.response import Response
from .models import User
from rest_framework import viewsets
from .serializers import TelemetrySerializer
from main.models import LoginPassword
from main.forms import LoginForm
from .utils import login_required


def login_view(request):
    error = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            if LoginPassword.objects.filter(password=password).exists():
                request.session['authenticated'] = True
                return redirect('main:dashboard')
            else:
                error = 'Invalid password'
    else:
        form = LoginForm()

    return render(request, 'main/login.html', {'form': form, 'error': error})


@login_required
def dashboard(request):
    users = User.objects.all()
    return render(request, 'main/dashboard.html', {'users': users})


@login_required
def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    telemetry = user.telemetry.all()

    coordinates = [
        {
            "latitude": data.latitude,
            "longitude": data.longitude,
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ambient_temperature": round(data.ambient_temperature, 2),
            "target_temperature": round(data.thermostat_target_temperature, 2),
            "current_temperature": round(data.thermostat_current_temperature, 2),
        }
        for data in telemetry
    ]


    if telemetry.exists():
        initial_location = [telemetry.first().latitude, telemetry.first().longitude]
    else:
        initial_location = [0, 0]

    map_folium = folium.Map(location=initial_location, zoom_start=13)

    # Добавляем маркеры на карту
    points = []
    for i, data in enumerate(telemetry):
        popup_content = f"""
        <div style="font-family: 'Raleway', sans-serif; font-size: 14px; color: #0a1005;">
            <strong>Time:</strong> {data.timestamp.strftime("%Y-%m-%d %H:%M")}<br>
            <strong>Ambient Temp:</strong> {data.ambient_temperature:.2f}°C<br>
            <strong>Target Temp:</strong> {data.thermostat_target_temperature:.2f}°C<br>
            <strong>Current Temp:</strong> {data.thermostat_current_temperature:.2f}°C
        </div>
        """

        # Добавляем маркер на карту
        folium.CircleMarker(
            location=[data.latitude, data.longitude],
            radius=6,
            color="#1EB32D",
            fill=True,
            fill_color="#1EB32D",
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=300),
            title=f"Marker {i}",  # Для отображения в UI
            id=f"marker-{i}",  # Для того чтобы идентифицировать маркеры
        ).add_to(map_folium)

        # Передаем маркеры в шаблон
        markers = [
            {
                "index": i,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "ambient_temperature": round(data.ambient_temperature, 2),
                "target_temperature": round(data.thermostat_target_temperature, 2),
                "current_temperature": round(data.thermostat_current_temperature, 2),
            }
            for i, data in enumerate(telemetry)
        ]

        points.append([data.latitude, data.longitude])

    if len(points) > 1:
        folium.PolyLine(points, color="#0a1005", weight=2.5, opacity=1).add_to(map_folium)

    map_html = map_folium._repr_html_()

    return render(request, 'main/user_details.html', {
        'user': user,
        'telemetry': telemetry,
        'map_html': map_html,
        'coordinates': coordinates,
        'markers': markers,  # Передаем маркеры в шаблон
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
