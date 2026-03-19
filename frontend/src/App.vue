<script setup lang="ts">
import { ref } from 'vue';
import Chart from 'chart.js/auto';

const city = ref('');
const loading = ref(false);
const error = ref('');

const summary = ref<any>(null);

const tempChartRef = ref<HTMLCanvasElement | null>(null);
const precipChartRef = ref<HTMLCanvasElement | null>(null);
const windChartRef = ref<HTMLCanvasElement | null>(null);
const uvChartRef = ref<HTMLCanvasElement | null>(null);

let charts: Chart[] = [];

const destroyCharts = () => {
  charts.forEach(c => c.destroy());
  charts = [];
};

const commonChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: {
      grid: { display: false, color: '#333' },
      ticks: { color: '#F0F0F0', maxTicksLimit: 12 }
    },
    y: {
      grid: { color: '#333' },
      ticks: { color: '#F0F0F0' }
    }
  },
  elements: {
    line: {
      tension: 0,
      borderWidth: 1.5,
      borderColor: '#F0F0F0'
    },
    point: {
      radius: 0,
      hitRadius: 10,
      hoverRadius: 4
    }
  }
};

const createChart = (ctx: HTMLCanvasElement, type: string, labels: string[], data: number[], label: string) => {
  const chart = new Chart(ctx, {
    type: type as any,
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: '#F0F0F0',
        backgroundColor: '#F0F0F0',
        borderWidth: 1.5,
        tension: 0,
        pointRadius: 0
      }]
    },
    options: JSON.parse(JSON.stringify(commonChartOptions)) as any
  });
  charts.push(chart);
};

const createPrecipChart = (ctx: HTMLCanvasElement, labels: string[], prob: number[], amount: number[]) => {
  const options: any = JSON.parse(JSON.stringify(commonChartOptions));
  options.scales.y = { type: 'linear', position: 'left', grid: { color: '#333' }, ticks: { color: '#F0F0F0' } };
  options.scales.y1 = { type: 'linear', position: 'right', display: true, grid: { display: false }, ticks: { color: '#888' } };
  
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Precipitation Amount (mm)',
          data: amount,
          borderColor: '#F0F0F0',
          backgroundColor: '#F0F0F0',
          type: 'bar',
          yAxisID: 'y'
        },
        {
          label: 'Probability (%)',
          data: prob,
          borderColor: '#888',
          borderWidth: 1.5,
          tension: 0,
          pointRadius: 0,
          yAxisID: 'y1'
        }
      ]
    },
    options
  });
  charts.push(chart);
};

const formatTime = (isoString: string) => {
  const d = new Date(isoString);
  const hours = d.getHours().toString().padStart(2, '0');
  const date = d.getDate().toString().padStart(2, '0');
  return `${date}/${hours}:00`;
};

const fetchWeather = async () => {
  if (!city.value) return;
  
  loading.value = true;
  error.value = '';
  destroyCharts();
  summary.value = null;

  try {
    const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city.value)}&count=1&format=json`);
    const geoData = await geoRes.json();
    
    if (!geoData.results || geoData.results.length === 0) {
      throw new Error("City not found");
    }
    
    const lat = geoData.results[0].latitude;
    const lon = geoData.results[0].longitude;

    const weatherRes = await fetch(`http://10.217.49.245:8000/?lat=${lat}&lon=${lon}`);
    if (!weatherRes.ok) throw new Error("Failed to fetch weather data");
    
    const weatherData = await weatherRes.json();
    
    summary.value = weatherData.summary;
    const hourly = weatherData.hourly;

    const slice = hourly.slice(0, 48);
    const labels = slice.map((h: any) => formatTime(h.date));
    
    const temps = slice.map((h: any) => h.temperature_2m);
    const precipProb = slice.map((h: any) => h.precipitation_probability);
    const precipAmt = slice.map((h: any) => h.precipitation);
    const windSpeed = slice.map((h: any) => h.wind_speed_10m);
    const uvIndex = slice.map((h: any) => h.uv_index);

    setTimeout(() => {
      if (tempChartRef.value) createChart(tempChartRef.value, 'line', labels, temps, 'Temperature (C)');
      if (windChartRef.value) createChart(windChartRef.value, 'line', labels, windSpeed, 'Wind Speed (km/h)');
      if (uvChartRef.value) createChart(uvChartRef.value, 'line', labels, uvIndex, 'UV Index');
      if (precipChartRef.value) createPrecipChart(precipChartRef.value, labels, precipProb, precipAmt);
    }, 50);

  } catch (e: any) {
    error.value = e.message || "An error occurred";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="root">
    <div class="inner app-container">
      <header class="header">
        <input 
          v-model="city" 
          @keyup.enter="fetchWeather" 
          placeholder="Enter city name..." 
          class="city-input"
        />
        <button @click="fetchWeather" class="fetch-btn" :disabled="loading">
          {{ loading ? 'LOADING...' : 'GET' }}
        </button>
      </header>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="summary" class="dashboard">
        <div class="metrics">
          <div class="metric-box">
            <span class="metric-label">TOTAL RAINFALL</span>
            <span class="metric-value">{{ summary.total_rainfall.toFixed(2) }} mm</span>
          </div>
          <div class="metric-box">
            <span class="metric-label">MIN TEMP</span>
            <span class="metric-value">{{ summary.min_temperature.toFixed(1) }} C</span>
          </div>
          <div class="metric-box">
            <span class="metric-label">MAX TEMP</span>
            <span class="metric-value">{{ summary.max_temperature.toFixed(1) }} C</span>
          </div>
          <div class="metric-box">
            <span class="metric-label">AVG TEMP</span>
            <span class="metric-value">{{ summary.avg_temperature.toFixed(1) }} C</span>
          </div>
        </div>

        <div class="charts-grid">
          <div class="chart-container">
            <div class="chart-title">TEMPERATURE VS TIME</div>
            <div class="canvas-wrapper"><canvas ref="tempChartRef"></canvas></div>
          </div>
          <div class="chart-container">
            <div class="chart-title">PRECIPITATION: PROBABILITY VS AMOUNT</div>
            <div class="canvas-wrapper"><canvas ref="precipChartRef"></canvas></div>
          </div>
          <div class="chart-container">
            <div class="chart-title">WIND SPEED TREND</div>
            <div class="canvas-wrapper"><canvas ref="windChartRef"></canvas></div>
          </div>
          <div class="chart-container">
            <div class="chart-title">UV INDEX CURVE</div>
            <div class="canvas-wrapper"><canvas ref="uvChartRef"></canvas></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  max-width: 1200px;
  width: 100%;
  padding: 2rem;
  box-sizing: border-box;
}

.header {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.city-input {
  flex: 1;
  background: transparent;
  border: 1px solid #444;
  color: #F0F0F0;
  padding: 0.75rem 1rem;
  font-family: inherit;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.city-input:focus {
  border-color: #F0F0F0;
}

.city-input::placeholder {
  color: #888;
}

.fetch-btn {
  background: #FFFFFF;
  color: #000000;
  border: none;
  padding: 0.75rem 2rem;
  font-family: inherit;
  font-weight: bold;
  cursor: pointer;
  font-size: 1rem;
  text-transform: uppercase;
  transition: opacity 0.2s;
}

.fetch-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.fetch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  color: #ff5555;
  margin-bottom: 2rem;
  padding: 1rem;
  border: 1px solid #ff5555;
}

.metrics {
  display: flex;
  gap: 3rem;
  margin-bottom: 4rem;
  flex-wrap: wrap;
  border-bottom: 1px solid #333;
  padding-bottom: 2rem;
}

.metric-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #888;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.metric-value {
  font-size: 2rem;
  color: #ff6700;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 4rem;
}

.chart-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.canvas-wrapper {
  height: 300px;
  position: relative;
  width: 100%;
}

.chart-title {
  font-size: 0.75rem;
  color: #00C0C0;
  letter-spacing: 0.1em;
  margin-bottom: 1rem;
  text-transform: uppercase;
  border-bottom: 1px solid #333;
  padding-bottom: 0.5rem;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .app-container {
    padding: 1rem;
  }
  
  .header {
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }
  
  .city-input, .fetch-btn {
    width: 100%;
    box-sizing: border-box;
  }
  
  .metrics {
    gap: 1.5rem;
    flex-wrap: wrap;
    margin-bottom: 2rem;
  }
  
  .metric-box {
    flex: 1 1 40%;
  }

  .metric-value {
    font-size: 1.5rem;
  }

  .charts-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .canvas-wrapper {
    height: 250px;
  }
}
</style>
