"""Descarga el clima diario del año agrícola 2025-2026 en cada región de Panamá (API de Open-Meteo).

Un punto por región: la cabecera o sede regional del MIDA (coordenadas del geocodificador de
Open-Meteo). Las regiones son las mismas de data/semiestructurado/*.json, para cruzar con la producción.

Ejecutar desde la raíz del repo: python scripts/descargar_clima.py
"""
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

INICIO, FIN = "2025-05-01", "2026-04-30"  # año agrícola 2025-2026
SALIDA = "data/estructurado/clima_diario_2025_2026.csv"

# shortcut: un solo punto por región; el café de Chiriquí está en altura (Boquete), no en David
LOCALIZACIONES = [
    {"region": "Bocas del Toro", "lugar": "Changuinola", "lat": 9.43, "lon": -82.52},
    {"region": "Chiriquí", "lugar": "David", "lat": 8.42729, "lon": -82.43085},
    {"region": "Coclé", "lugar": "Penonomé", "lat": 8.51889, "lon": -80.35727},
    {"region": "Colón", "lugar": "Colón", "lat": 9.36025, "lon": -79.90019},
    {"region": "Comarca Ngäbe Buglé", "lugar": "Llano Tugrí", "lat": 8.47927, "lon": -81.71211},
    {"region": "Darién", "lugar": "Metetí", "lat": 8.49909, "lon": -77.97897},
    {"region": "Herrera", "lugar": "Chitré", "lat": 7.96011, "lon": -80.42876},
    {"region": "Los Santos", "lugar": "Las Tablas", "lat": 7.7665, "lon": -80.27798},
    {"region": "Panamá Este", "lugar": "Chepo", "lat": 9.17019, "lon": -79.10083},
    {"region": "Panamá Oeste", "lugar": "La Chorrera", "lat": 8.87763, "lon": -79.78007},
    {"region": "Veraguas", "lugar": "Santiago", "lat": 8.1, "lon": -80.98333},
]

# El orden importa: la API devuelve las variables en este mismo orden
VARIABLES = ["precipitation_sum", "precipitation_hours", "temperature_2m_max", "temperature_2m_min",
             "temperature_2m_mean"]


def obtener_clima():
    # Cliente de Open-Meteo con caché y reintentos
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    params = {
        "latitude": [l["lat"] for l in LOCALIZACIONES],
        "longitude": [l["lon"] for l in LOCALIZACIONES],
        "start_date": INICIO,
        "end_date": FIN,
        "daily": VARIABLES,
        "timezone": "America/Panama",
    }
    # Una respuesta por localización, en el mismo orden de LOCALIZACIONES
    responses = openmeteo.weather_api("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params)

    tablas = []
    for loc, response in zip(LOCALIZACIONES, responses):
        daily = response.Daily()
        df = pd.DataFrame({v: daily.Variables(i).ValuesAsNumpy() for i, v in enumerate(VARIABLES)})
        df.insert(0, "fecha", pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        ).tz_convert("America/Panama").date)
        df.insert(1, "region", loc["region"])
        df.insert(2, "lugar", loc["lugar"])
        df.insert(3, "elevacion_m", response.Elevation())
        tablas.append(df)
    return pd.concat(tablas, ignore_index=True).round(2)


if __name__ == "__main__":
    df = obtener_clima()
    # Autochequeo: un año completo de datos por región
    dias = df.groupby("region").size()
    assert len(dias) == len(LOCALIZACIONES) and (dias == 365).all(), dias
    df.to_csv(SALIDA, index=False)
    print(f"{len(df)} filas -> {SALIDA}")
    print(df.groupby("region")[VARIABLES[0]].sum().round(0).rename("lluvia_anual_mm"))
