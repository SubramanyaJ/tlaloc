# coding=ISO-8859-1
import codecs
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main(lat: float, lon: float):
    ## Setup a connection
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Process
    # Pack to JSON

    ## Get weather data
    # Obtain this directly from the documentation
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "precipitation_probability", "precipitation", "rain", "wind_speed_10m", "uv_index"],
    }
    responses = openmeteo.weather_api(url, params=params)

    # Multiple responses can be parsed with a for loop
    # However, I will always request a single location
    # This way, API calls are reduced
    response = responses[0]
    res_lat, res_lon = response.Latitude(), response.Longitude()
    res_ele = response.Elevation()

    ## Unpack data
    # Parsing the hourly data.
    # Obtained in the order in which they are requested
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_rain = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_uv_index = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["rain"] = hourly_rain
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["uv_index"] = hourly_uv_index

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # DONE Precipitation probability vs precipitation (chart.js)
    # DONE UV index curve (chart.js)
    # DONE Wind speed trend (chart.js)
    # DONE Temperature vs time (chart.js)
    # DONE Total rainfall
    # DONE Min Max Avg Temperature

    min_temp = min(hourly_data["temperature_2m"])
    max_temp = max(hourly_data["temperature_2m"])
    total_rainfall = sum(hourly_data["precipitation"])

    avg_temp = sum(hourly_data["temperature_2m"]) / len(hourly_data["temperature_2m"])
    stats = {
        "min_temperature" : float(min_temp),
        "max_temperature" : float(max_temp),
        "avg_temperature" : float(avg_temp),
        "total_rainfall" : float(total_rainfall)
    }

    res = hourly_dataframe.to_dict(orient="records")

    return {
        "location": {
            "lat": res_lat,
            "lon": res_lon,
            "elevation": res_ele
        },
        "summary": stats,
        "hourly": res
    }
