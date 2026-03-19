<script setup lang="ts">

const apiUrl = "127.0.0.1:8000";

fetch("http://127.0.0.1:8000/")
  .then(response => response.json())
  .then(data => {
    console.log(data);
  })
  .catch(error => {
    console.error(error);
  });

const ctx = document.getElementById('tempChart').getContext('2d');

const tempChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], // time axis
        datasets: [{
            label: 'Temperature (°C)',
            data: [28, 30, 29, 31, 33, 32, 34], // temperature values
            borderWidth: 2,
            tension: 0.3, // smooth curve
            fill: false
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Weekly Temperature'
            }
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Day'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Temperature (°C)'
                },
                beginAtZero: false
            }
        }
    }
});

</script>

<template>
  <div class="root">



  </div>
</template>
