import json
import re
from datetime import datetime

import requests
from django.db.models import Avg, StdDev, Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
import folium
from django.utils import timezone
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from .models import User, Telemetry, WeatherData
from rest_framework import viewsets, serializers, status
from .serializers import TelemetrySerializer, TelemetryDataSerializer
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


geo_pattern = re.compile(r'^-?\d{1,2}\.\d{6}$')


def validate_geoposition(lat, long):
    try:
        lat = float(lat)
        long = float(long)
    except ValueError:
        return False

    if not geo_pattern.match(f"{lat:.6f}") or not (-90 <= lat <= 90):
        return False
    if not geo_pattern.match(f"{long:.6f}") or not (-180 <= long <= 180):
        return False

    return True


def fetch_weather():
    try:
        response = requests.get(
            'https://api.weatherapi.com/v1/current.json',
            params={'key': '17984325ba0f4898b36113347242512', 'q': 'Helsinki', 'lang': 'eng'}
        )
        response.raise_for_status()
        data = response.json()

        location = data.get('location', {})
        current = data.get('current', {})
        condition = current.get('condition', {})

        if not location or not current or not condition:
            raise ValueError("Invalid data format in API response")

        WeatherData.objects.create(
            location=location.get('name', 'Unknown'),
            temperature=current.get('temp_c', 0.0),
            condition=condition.get('text', 'Unknown'),
            humidity=current.get('humidity', 'Unknown'),
            wind_speed=current.get('wind_kph', 'Unknown'),
            last_updated=now()
        )
        print(f"Weather data for {location.get('name', 'Unknown')} saved successfully.")
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
    except KeyError as e:
        print(f"Missing key in API response: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


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
    print("Date from is", date_from)
    print("Date to is", date_to)

    date_from, date_to = process_dates(date_from, date_to)
    print("Date from processed is", date_from)
    print("Date to processed is", date_to)

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
    # print("Date from is", date_from)
    # print("Date to is", date_to)

    date_from, date_to = process_dates(date_from, date_to)
    # print("Date from processed is", date_from)
    # print("Date to processed is", date_to)

    telemetry = user.telemetry.all()
    if date_from and date_to:
        telemetry = telemetry.filter(
            timestamp__gte=date_from,
            timestamp__lte=date_to
        )

    average_ambient_temperature = telemetry.aggregate(Avg('ambient_temperature'))['ambient_temperature__avg'] or 0
    average_target_temperature = telemetry.aggregate(Avg('thermostat_target_temperature'))[
                                     'thermostat_target_temperature__avg'] or 0
    average_current_temperature = telemetry.aggregate(Avg('thermostat_current_temperature'))[
                                      'thermostat_current_temperature__avg'] or 0

    stddev_ambient_temperature = telemetry.aggregate(StdDev('ambient_temperature'))['ambient_temperature__stddev'] or 0
    stddev_target_temperature = telemetry.aggregate(StdDev('thermostat_target_temperature'))[
                                    'thermostat_target_temperature__stddev'] or 0
    stddev_current_temperature = telemetry.aggregate(StdDev('thermostat_current_temperature'))[
                                     'thermostat_current_temperature__stddev'] or 0

    coordinates = [
        {
            "latitude": data.latitude,
            "longitude": data.longitude,
            "timestamp": data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ambient_temperature": round(data.ambient_temperature, 2),
            "target_temperature": round(data.thermostat_target_temperature, 2),
            "current_temperature": round(data.thermostat_current_temperature, 2),
        }
        for data in sorted(telemetry, key=lambda x: x.timestamp)
    ]

    # print("Coordinates are:", coordinates)

    if telemetry.exists():
        initial_location = [telemetry.first().latitude, telemetry.first().longitude]
    else:
        initial_location = [0, 0]

    map_folium = folium.Map(location=initial_location, zoom_start=13)
    points = []
    markers = []
    sorted_telemetry = sorted(telemetry, key=lambda x: x.timestamp)
    for i, data in enumerate(sorted_telemetry, start=1):
        popup_content = f"""
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600&display=swap" rel="stylesheet">
        </head>
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

        folium.map.Marker(
            [data.latitude, data.longitude],
            icon=folium.DivIcon(
                html=f"""
                <head>
                    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600&display=swap" rel="stylesheet">
                </head>
                <div style="font-family: 'Raleway', sans-serif; font-size: 14px; font-weight: bold; color: black; text-align: center;">{i}</div>
                """
            )
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

    fetch_weather()

    current_weather = WeatherData.objects.order_by('-last_updated').first()
    print("Current weather is:", current_weather)

    return render(request, 'main/user_details.html', {
        'user': user,
        'telemetry': telemetry,
        'map_html': map_html,
        'coordinates': json.dumps(coordinates),
        'date_from': date_from,
        'date_to': date_to,
        'markers': json.dumps(markers),
        'average_ambient_temperature': round(average_ambient_temperature, 2),
        'average_target_temperature': round(average_target_temperature, 2),
        'average_current_temperature': round(average_current_temperature, 2),
        'stddev_ambient_temperature': round(stddev_ambient_temperature, 2),
        'stddev_target_temperature': round(stddev_target_temperature, 2),
        'stddev_current_temperature': round(stddev_current_temperature, 2),
        'current_weather': current_weather,
    })


# @csrf_exempt
class ClientDataView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"detail": "GET method is not supported for this endpoint."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        # Use request.data to get JSON body of the POST request
        print("POST detected in ClisenDataView")
        serializer = TelemetryDataSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client_id = data['client_id']

            user, created = User.objects.get_or_create(
                email=f"user{client_id}@keho.test",  # Create an email for the user based on client_id
            )

            # If the user was created, you might want to log it
            if created:
                print(f"User with email {user.email} and ID {client_id} was created.")

            # Get the last d_time for the client
            last_d_time = Telemetry.objects.filter(user=user).aggregate(Max('d_time'))['d_time__max']
            print("Last d time form db:", last_d_time)
            if last_d_time is None:
                last_d_time = -1

            print("Current last_d_time is:", last_d_time)

            # Save the first telemetry data
            Telemetry.objects.get_or_create(
                user=user,
                timestamp=data['first_time'],
                d_time=last_d_time + 1,
                defaults={
                    'latitude': data['first_lat'],
                    'longitude': data['first_long'],
                    'ambient_temperature': data['first_ambT'],
                    'thermostat_current_temperature': data['first_curT'],
                    'thermostat_target_temperature': data['first_trgT'],
                }
            )

            last_d_time += 1
            print("Firstt last_d_time for data is:", last_d_time)

            # Save the rest of the telemetry data
            for telemetry in data['d']:
                d_time = telemetry['dTime']
                d_lat = telemetry['dLat']
                d_long = telemetry['dLong']
                ambT = telemetry['ambT']
                curT = telemetry['curT']
                trgT = telemetry['targT']

                if validate_geoposition(d_lat, d_long):
                    Telemetry.objects.get_or_create(
                        user=user,
                        timestamp=data['first_time'],
                        d_time=d_time,
                        defaults={
                            'latitude': d_lat,
                            'longitude': d_long,
                            'ambient_temperature': ambT,
                            'thermostat_current_temperature': curT,
                            'thermostat_target_temperature': trgT,
                        }
                    )
                else:
                    print(f"Invalid geo: latitude={d_lat}, longitude={d_long}")

                last_d_time += 1
                print("last_d_time for the rest of data:", last_d_time)

            # Fetch the latest weather data
            weather_data = WeatherData.objects.order_by('-last_updated').first()
            if weather_data:
                response_data = {
                    "curT": weather_data.temperature,
                    "condition": weather_data.condition
                }
            else:
                response_data = {
                    "curT": 0,
                    "condition": "Unknown"
                }

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TelemetryDataViewSet(ViewSet):
    def create(self, request):
        serializer = TelemetryDataSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Data processed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# def exchange_data(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         telemetry = Telemetry.objects.create(
#             latitude=data.get('first_lat'),
#             longitude=data.get('first_long'),
#             timestamp=data.get('first_time'),
#             ambient_temperature=data.get('first_ambT'),
#             thermostat_target_temperature=data.get('first_trgT'),
#             thermostat_current_temperature=data.get('first_curT'),
#         )
#
#         latest_weather = WeatherData.objects.latest('last_updated')
#         response_data = {
#             "curT": latest_weather.temperature,
#             "condition": latest_weather.condition
#         }
#         return JsonResponse(response_data, status=200)
#
#     return JsonResponse({"error": "Invalid method"}, status=400)


# class TelemetryViewSet(viewsets.ViewSet):
#     def create(self, request):
#         email = request.data.get('email')
#         user, _ = User.objects.get_or_create(email=email)
#
#         telemetry_data = {
#             'user': user.id,
#             'latitude': request.data.get('latitude'),
#             'longitude': request.data.get('longitude'),
#             'ambient_temperature': request.data.get('ambient_temperature'),
#             'thermostat_target_temperature': request.data.get('thermostat_target_temperature'),
#             'thermostat_current_temperature': request.data.get('thermostat_current_temperature'),
#         }
#
#         serializer = TelemetrySerializer(data=telemetry_data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"status": "success", "data": serializer.data})
