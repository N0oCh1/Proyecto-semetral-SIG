import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

def obtener_clima(): 
  # Setup the Open-Meteo API client with cache and retry on error
  cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
  retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
  openmeteo = openmeteo_requests.Client(session = retry_session)

  # Make sure all required weather variables are listed here
  # The order of variables in hourly or daily is important to assign them correctly below
  url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
  params = {
    "latitude": 9,
    "longitude": -80,
    "start_date": "2011-01-01",
    "end_date": "2023-12-30",
    "daily": ["sunrise", "precipitation_hours", "temperature_2m_max", "temperature_2m_min", "weather_code"],
    "timezone": "auto",
  }
  responses = openmeteo.weather_api(url, params = params)

  # Process first location. Add a for-loop for multiple locations or weather models
  response = responses[0]
  print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
  print(f"Elevation: {response.Elevation()} m asl")
  print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
  print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

  # Process daily data. The order of variables needs to be the same as requested.
  daily = response.Daily()
  daily_sunrise = daily.Variables(0).ValuesInt64AsNumpy()
  daily_precipitation_hours = daily.Variables(1).ValuesAsNumpy()
  daily_temperature_2m_max = daily.Variables(2).ValuesAsNumpy()
  daily_temperature_2m_min = daily.Variables(3).ValuesAsNumpy()
  daily_weather_code = daily.Variables(4).ValuesAsNumpy()

  daily_data = {
    "date": pd.date_range(
      start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
      end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
      freq = pd.Timedelta(seconds = daily.Interval()),
      inclusive = "left"
    ).tz_convert(response.Timezone().decode())
  }

  daily_data["sunrise"] = pd.to_datetime(daily_sunrise, unit = "s", utc = True).tz_convert(response.Timezone().decode())
  daily_data["precipitation_hours"] = daily_precipitation_hours
  daily_data["temperature_2m_max"] = daily_temperature_2m_max
  daily_data["temperature_2m_min"] = daily_temperature_2m_min
  daily_data["weather_code"] = daily_weather_code

  daily_dataframe = pd.DataFrame(data = daily_data)
  print("\nDaily data\n", daily_dataframe)
  return daily_dataframe



