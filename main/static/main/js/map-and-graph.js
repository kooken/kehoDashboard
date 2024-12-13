const ctx = document.getElementById('temperatureChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: telemetry.map(c => c.timestamp),
        datasets: [
            {
                label: 'Ambient',
                data: telemetry.map(c => c.ambient_temperature),
                borderColor: 'blue',
                backgroundColor: 'blue',
                borderWidth: 2,
                pointBackgroundColor: 'blue',
                pointBorderColor: 'blue',
                tension: 0.4,
                fill: false,
            },
            {
                label: 'Target',
                data: telemetry.map(c => c.target_temperature),
                borderColor: 'green',
                backgroundColor: 'green',
                borderWidth: 2,
                pointBackgroundColor: 'green',
                pointBorderColor: 'green',
                tension: 0.4,
                fill: false,
            },
            {
                label: 'Current',
                data: telemetry.map(c => c.current_temperature),
                borderColor: 'red',
                backgroundColor: 'red',
                borderWidth: 2,
                pointBackgroundColor: 'red',
                pointBorderColor: 'red',
                tension: 0.4,
                fill: false,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Timestamp',
                    color: '#4CAF50',
                    font: {
                        size: 14,
                        family: 'Raleway',
                        weight: 'bold',
                    },
                },
                ticks: {
                        color: '#0a1005',
                        font: {
                            size: 12,
                            family: 'Raleway',
                        },
                        callback: function (value, index) {
                            const originalDate = telemetry[index].timestamp;
                            const date = new Date(originalDate);
                            const formattedDate = `${date.getDate().toString().padStart(2, '0')}.${(date.getMonth() + 1).toString().padStart(2, '0')}.${date.getFullYear().toString().slice(-2)} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
                            return formattedDate;
                        },
                    },
            },
            y: {
                title: {
                    display: true,
                    text: 'Temperature (°C)',
                    color: '#4CAF50',
                    font: {
                        size: 14,
                        family: 'Raleway',
                        weight: 'bold',
                    },
                },
            },
        },
        plugins: {
            legend: {
                labels: {
                    color: '#0a1005',
                    font: {
                        size: 14,
                        family: 'Raleway',
                        weight: 'bold',
                    },
                },
            },
            tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#F9FCF8',
                    bodyColor: '#F9FCF8',
                    borderWidth: 1,
                    borderColor: '#F9FCF8',
                    titleFont: {
                        family: 'Raleway',
                        size: 12,
                        weight: 'bold',
                    },
                    bodyFont: {
                        family: 'Raleway',
                        size: 12,
                    },
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.raw !== null) {
                                label += context.raw.toFixed(2) + '°C';
                            }
                            return label;
                        },
                    },
                },
            annotation: {
                annotations: []
            }
        },
    },
});