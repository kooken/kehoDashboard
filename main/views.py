import json
import re
import requests
import folium
import logging
from datetime import datetime, timedelta

from django.core.mail import mail_admins
from django.db import connection
from django.db.models import Avg, StdDev, Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.timezone import now, make_aware, is_naive
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from .models import User, Telemetry, WeatherData
from rest_framework import viewsets, serializers, status

from .queries import lost_minutes_query
from .serializers import TelemetrySerializer, TelemetryDataSerializer
from main.models import LoginPassword
from main.forms import LoginForm
from .utils import login_required

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('weather_fetch.log')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def process_dates(date_from_str, date_to_str):
    if date_from_str and date_to_str:
        try:
            if "T" in date_from_str and "T" in date_to_str:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%dT%H:%M")
                date_to = datetime.strptime(date_to_str, "%Y-%m-%dT%H:%M")
            else:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d")

            date_from = timezone.make_aware(date_from)
            date_to = timezone.make_aware(date_to)

            if date_from.date() == date_to.date() and "T" not in date_to_str:
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
        error_message = f"API Request failed: {e}"
        print(error_message)
        mail_admins(
            subject="Weather API Request Error",
            message=f"An error occurred during the API request: {e}",
            fail_silently=False,
        )

    except KeyError as e:
        error_message = f"Missing key in API response: {e}"
        print(error_message)
        mail_admins(
            subject="Weather API Missing Key Error",
            message=f"A missing key error occurred: {e}",
            fail_silently=False,
        )

    except OSError as e:
        error_message = f"OSError occurred: {e}"
        print(error_message)
        mail_admins(
            subject="OSError in Weather Fetching",
            message=f"An OSError occurred during weather fetching: {e}",
            fail_silently=False,
        )

    except Exception as e:
        error_message = f"An unknown error occurred: {e}"
        print(error_message)
        mail_admins(
            subject="Unknown Error in Weather Fetching",
            message=f"An unknown error occurred: {e}",
            fail_silently=False,
        )


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


# @login_required
def dashboard(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    # print("Date from is", date_from)
    # print("Date to is", date_to)

    date_from, date_to = process_dates(date_from, date_to)
    # print("Date from processed is", date_from)
    # print("Date to processed is", date_to)

    users = User.objects.all()
    for user in users:
        user.short_email = user.email.split('@')[0]

    with connection.cursor() as cursor:
        cursor.execute(lost_minutes_query)
        results = cursor.fetchall()
        columns = [col[0] for col in cursor.description]  # Get column names

    # Prepare data for template
    lost_data = [dict(zip(columns, row)) for row in results]

    for user in users:
        user.telemetry_filtered = user.telemetry.filter(timestamp__gte=date_from,
                                                        timestamp__lte=date_to) if date_from and date_to else user.telemetry.all()

    return render(request, 'main/dashboard.html', {
        'users': users,
        'date_from': date_from,
        'date_to': date_to,
        'lost_data': lost_data,
    })


# @login_required
def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Debugging raw input
    # print("Raw GET parameters:", request.GET)
    # print("User Date from is", date_from)
    # print("User Date to is", date_to)

    # Processing dates
    date_from, date_to = process_dates(date_from, date_to)
    # print("User Date from processed is", date_from)
    # print("User Date to processed is", date_to)

    telemetry = user.telemetry.all()
    if date_from and date_to:
        telemetry = telemetry.filter(
            timestamp__gte=date_from,
            timestamp__lte=date_to
        )

    telemetry_sorted = sorted(telemetry, key=lambda x: x.timestamp, reverse=True)

    telemetry_data = []
    for t in telemetry_sorted[:50]:
        telemetry_data.append({
            'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'target_temperature': round(t.thermostat_target_temperature, 2),
            'current_temperature': round(t.thermostat_current_temperature, 2),
            'ambient_temperature': round(t.ambient_temperature, 2),
            'mode': t.mode
        })

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
    # print("Current weather is:", current_weather)

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
        'telemetry_data': telemetry_data,
    })


# @csrf_exempt
class ClientDataView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"detail": "GET method is not supported for this endpoint."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        # Use request.data to get JSON body of the POST request
        print("POST detected in ClientDataView")
        serializer = TelemetryDataSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client_id = data['client_id']

            user, created = User.objects.get_or_create(
                email=f"user{client_id}@keho.test",  # Create an email for the user based on client_id
            )

            # Log user creation
            if created:
                print(f"User with email {user.email} and ID {client_id} was created.")

            # Get the last values_counter for the client
            last_values_counter = Telemetry.objects.filter(user=user).aggregate(Max('values_counter'))[
                'values_counter__max']
            print("Last values_counter from db:", last_values_counter)
            if last_values_counter is None:
                last_values_counter = -1

            print("Current last_values_counter is:", last_values_counter)

            if isinstance(data['first_time'], str):
                try:
                    first_time_object = datetime.strptime(data['first_time'], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print(f"Error parsing date: {data['first_time']}")
            elif isinstance(data['first_time'], datetime):
                first_time_object = data['first_time']
            else:
                print("Unexpected type for 'first_time'. It is not a string or datetime.")

            print("Converted first time is:", first_time_object)

            # first_time_object = datetime.strptime(data['first_time'], "%Y-%m-%d %H:%M:%S")
            # print("Converted first time is:", first_time_object)
            if is_naive(first_time_object):
                timestamp_first_aware = make_aware(first_time_object)
            else:
                timestamp_first_aware = first_time_object
            # Save the first telemetry data
            Telemetry.objects.get_or_create(
                user=user,
                timestamp=timestamp_first_aware,
                values_counter=last_values_counter + 1,
                defaults={
                    'latitude': data['first_lat'],
                    'longitude': data['first_long'],
                    'ambient_temperature': data['first_ambT'],
                    'thermostat_current_temperature': data['first_curT'],
                    'thermostat_target_temperature': data['first_trgT'],
                    'mode': data['first_mode'],
                }
            )
            print("User saved to database: ", user)
            last_values_counter += 1
            print("First last_values_counter for data is:", last_values_counter)

            # Save the rest of the telemetry data
            for telemetry in data['d']:
                # d_time = telemetry['dTime']
                # d_lat = telemetry['dLat']
                # d_long = telemetry['dLong']
                # ambT = telemetry['ambT']
                # curT = telemetry['curT']
                # trgT = telemetry['targT']
                # d_time = telemetry['dTime']
                d_time_seconds = int(telemetry['dTime'])
                sample_time_object = first_time_object + timedelta(seconds=d_time_seconds)
                # sample_time_object = first_time_object + timedelta(seconds=telemetry['dTime'])
                d_lat = data['first_lat'] + telemetry['dLat'] / 1000000
                d_long = data['first_long'] + telemetry['dLong'] / 1000000
                ambT = data['first_ambT'] + telemetry['ambT'] / 100
                curT = data['first_curT'] + telemetry['curT'] / 100
                trgT = data['first_trgT'] + telemetry['targT'] / 100
                mode = str(telemetry.get('mode', 'off'))
                print(f"Mode received in telemetry: {mode}")

                print(
                    f"Saved to database: time {sample_time_object}\n"
                    f"user {user.display_name}\n"
                    f"mode {mode}\n"
                    f"latitude {d_lat}\n"
                    f"longitude {d_long}\n"
                    f"ambient temp {ambT}\n"
                    f"current temp {curT}\n"
                    f"target temp {trgT}\n")

                if is_naive(sample_time_object):
                    timestamp_aware = make_aware(sample_time_object)
                else:
                    timestamp_aware = sample_time_object

                if validate_geoposition(d_lat, d_long):
                    telemetry_record, created = Telemetry.objects.get_or_create(
                        user=user,
                        timestamp=timestamp_aware,
                        values_counter=last_values_counter,
                        defaults={
                            'latitude': d_lat,
                            'longitude': d_long,
                            'ambient_temperature': ambT,
                            'thermostat_current_temperature': curT,
                            'thermostat_target_temperature': trgT,
                            'mode': mode,
                        }
                    )
                    print("Mode saved to database: ", telemetry_record.mode)
                else:
                    print(f"Invalid geolocation: latitude={d_lat}, longitude={d_long}")

                last_values_counter += 1
                print("last_values_counter for the rest of data:", last_values_counter)

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


def test_error(request):
    try:
        raise OSError("Test error")
    except OSError as e:
        mail_admins(
            subject="Test Error Notification",
            message=f"An error occurred: {e}",
        )
        return HttpResponse("An error was raised and admins were notified.")
