# Telemetry Dashboard

This project is a **Telemetry Monitoring Dashboard**, designed for visualizing and analyzing telemetry data from IoT devices. The system includes real-time mapping, graphical data representation, and weather forecasting functionalities.

---

## Features
- **User Telemetry Tracking:** Displays telemetry data with timestamps, including coordinates and temperature metrics.
- **Interactive Map Visualization:** Shows the device's location and data points with detailed popups.
- **Graphical Insights:** Temperature trends displayed in a responsive chart.
- **Weather Forecast Integration:** Fetches and displays weather predictions based on the latest device coordinates.
- **Responsive Design:** Adapts seamlessly to various screen sizes for an enhanced user experience.

---

## Tech Stack
- **Backend:** Python, Django, Django REST Framework
- **Frontend:** HTML, CSS, JavaScript, Folium
- **Database:** PostgreSQL
- **API Integration:** OpenWeatherMap (for weather forecasts)

---

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/kooken/kehoDashboard.git
   ```
2. Navigate to the project directory:
   ```bash
   cd kehoDashboard
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Apply migrations and run the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
6. Access the dashboard at `http://127.0.0.1:8000/`.

---

## API Documentation
- **Swagger UI** is available at `http://127.0.0.1:8000/api/docs/`.
- Key endpoints:
  - `/api/telemetry/` — Submit and retrieve telemetry data.
  - `/api/weather/` — Fetch weather forecast data.

---

## About the Author
Hi! I'm **Maria Sazhina**, a co-founder and Head of R&D at **KehoSense Oy**, a startup specializing in advanced IoT solutions for smart environments. My expertise lies in developing robust systems for real-time data analysis, API integration, and innovative web-based applications.  

Feel free to reach out for collaboration or feedback! 😊
