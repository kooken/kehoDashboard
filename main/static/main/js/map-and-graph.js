const telemetry = {{ coordinates|safe }};

const ctx = document.getElementById('temperatureChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: telemetry.map(c => c.timestamp),
        datasets: [
            { label: 'Ambient', data: telemetry.map(c => c.ambient_temperature), borderColor: 'blue', fill: false },
            { label: 'Target', data: telemetry.map(c => c.target_temperature), borderColor: 'green', fill: false },
            { label: 'Current', data: telemetry.map(c => c.current_temperature), borderColor: 'red', fill: false },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { title: { display: true, text: 'Timestamp' } },
            y: { title: { display: true, text: 'Temperature (°C)' } }
        }
    },
});

function highlightChartSegment(index) {
    chart.data.datasets.forEach(dataset => {
        dataset.backgroundColor = dataset.data.map((_, i) =>
            i === index ? 'rgba(255, 99, 132, 0.5)' : 'rgba(0, 0, 0, 0.1)'
        );
    });
    chart.update();
}

function resetChartHighlight() {
    chart.data.datasets.forEach(dataset => {
        dataset.backgroundColor = 'rgba(0, 0, 0, 0.1)';
    });
    chart.update();
}

document.querySelectorAll('.leaflet-marker-icon').forEach((marker, index) => {
    marker.addEventListener('mouseover', () => highlightChartSegment(index));
    marker.addEventListener('mouseout', resetChartHighlight);
});