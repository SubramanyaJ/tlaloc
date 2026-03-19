import express from 'express';
import cors from 'cors';

const app = express();
app.use(cors());

app.get('/', async (req, res) => {
    try {
        const lat = parseFloat(req.query.lat);
        const lon = parseFloat(req.query.lon);

        if (isNaN(lat) || isNaN(lon)) {
            return res.status(400).json({ error: "Invalid lat or lon parameters" });
        }

        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=temperature_2m,precipitation_probability,precipitation,rain,wind_speed_10m,uv_index`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Open-Meteo API responded with status: ${response.status}`);
        }
        
        const data = await response.json();

        // compute stats
        const hourly = data.hourly;
        const times = hourly.time;
        const temps = hourly.temperature_2m;
        const precips = hourly.precipitation;
        
        let min_temp = Infinity;
        let max_temp = -Infinity;
        let sum_temp = 0;
        let total_rainfall = 0;

        const hourly_res = [];

        for (let i = 0; i < times.length; i++) {
            const temp = temps[i];
            const precip = precips[i];
            
            if (temp !== null && temp !== undefined) {
                if (temp < min_temp) min_temp = temp;
                if (temp > max_temp) max_temp = temp;
                sum_temp += temp;
            }
            if (precip !== null && precip !== undefined) {
                total_rainfall += precip;
            }

            hourly_res.push({
                date: new Date(times[i] + 'Z'),
                temperature_2m: temps[i],
                precipitation_probability: hourly.precipitation_probability[i],
                precipitation: precips[i],
                rain: hourly.rain[i],
                wind_speed_10m: hourly.wind_speed_10m[i],
                uv_index: hourly.uv_index[i]
            });
        }

        const validTempsCount = temps.filter(t => t !== null && t !== undefined).length;
        const avg_temp = validTempsCount > 0 ? sum_temp / validTempsCount : 0;

        res.json({
            location: {
                lat: data.latitude,
                lon: data.longitude,
                elevation: data.elevation
            },
            summary: {
                min_temperature: min_temp === Infinity ? 0 : min_temp,
                max_temperature: max_temp === -Infinity ? 0 : max_temp,
                avg_temperature: avg_temp,
                total_rainfall: total_rainfall
            },
            hourly: hourly_res
        });

    } catch (error) {
        console.error("Error fetching weather data:", error);
        res.status(500).json({ error: error.message });
    }
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
});
