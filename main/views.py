from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
import folium
from django.utils import timezone
from rest_framework.response import Response
from .models import User
from rest_framework import viewsets
from .serializers import TelemetrySerializer
from main.models import LoginPassword
from main.forms import LoginForm
from .utils import login_required


def process_dates(date_from_str, date_to_str):
    if date_from_str and date_to_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
            date_from = timezone.make_aware(date_from)
            date_to = timezone.make_aware(date_to)

            if date_from == date_to:
                date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)

            return date_from, date_to
        except ValueError:
            return None, None
    return None, None


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
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    date_from, date_to = process_dates(date_from, date_to)

    users = User.objects.all()

    for user in users:
        user.telemetry_filtered = user.telemetry.filter(timestamp__gte=date_from,
                                                        timestamp__lte=date_to) if date_from and date_to else user.telemetry.all()

    return render(request, 'main/dashboard.html', {
        'users': users,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    date_from, date_to = process_dates(date_from, date_to)

    telemetry = user.telemetry.all()
    if date_from and date_to:
        telemetry = telemetry.filter(
            timestamp__gte=date_from,
            timestamp__lte=date_to
        )

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
    points = []
    markers = []
    for i, data in enumerate(telemetry):
        popup_content = f"""
        <div style="font-family: 'Raleway', sans-serif; font-size: 14px; color: #0a1005;">
            <strong>Time:</strong> {data.timestamp.strftime("%Y-%m-%d %H:%M")}<br>
            <strong>Ambient Temp:</strong> {data.ambient_temperature:.2f}°C<br>
            <strong>Target Temp:</strong> {data.thermostat_target_temperature:.2f}°C<br>
            <strong>Current Temp:</strong> {data.thermostat_current_temperature:.2f}°C
        </div>
        """
        folium.CircleMarker(
            location=[data.latitude, data.longitude],
            radius=6,
            color="#1EB32D",
            fill=True,
            fill_color="#1EB32D",
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=300),
        ).add_to(map_folium)

        markers.append({
            "index": i,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ambient_temperature": round(data.ambient_temperature, 2),
            "target_temperature": round(data.thermostat_target_temperature, 2),
            "current_temperature": round(data.thermostat_current_temperature, 2),
        })

        points.append([data.latitude, data.longitude])

    if len(points) > 1:
        folium.PolyLine(points, color="#0a1005", weight=2.5, opacity=1).add_to(map_folium)

    map_html = map_folium._repr_html_()

    return render(request, 'main/user_details.html', {
        'user': user,
        'telemetry': telemetry,
        'map_html': map_html,
        'coordinates': coordinates,
        'date_from': date_from,
        'date_to': date_to,
        'markers': markers,
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
