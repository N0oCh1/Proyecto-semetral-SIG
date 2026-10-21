"""Asigna una fecha simulada (2016-2017) a cada reseña de TripAdvisor.

Cada día recibe al menos MIN_POR_DIA reseñas; el resto se reparte según la
demanda hotelera del mes (cuartos ocupados diarios) de hoteles_panama_2016_2017.csv.
"""
import numpy as np
import pandas as pd

MIN_POR_DIA = 10
SEMILLA = 2017

reviews = pd.read_csv("data/tripadvisor_hotel_reviews.csv")
hoteles = pd.read_csv("data/hoteles_panama_2016_2017.csv")

dias = pd.DataFrame({"Fecha": pd.date_range("2016-01-01", "2017-12-31", freq="D")})
dias["anio"], dias["mes"] = dias.Fecha.dt.year, dias.Fecha.dt.month
dias = dias.merge(hoteles[["anio", "mes", "cuartos_ocupados_diario"]], on=["anio", "mes"])

extra = len(reviews) - MIN_POR_DIA * len(dias)
assert extra >= 0, "no hay suficientes reseñas para el mínimo diario"

rng = np.random.default_rng(SEMILLA)
peso = dias.cuartos_ocupados_diario / dias.cuartos_ocupados_diario.sum()
por_dia = MIN_POR_DIA + rng.multinomial(extra, peso)

fechas = np.repeat(dias.Fecha.values, por_dia)
reviews = reviews.sample(frac=1, random_state=SEMILLA).reset_index(drop=True)
reviews["Fecha"] = fechas
reviews = reviews.sort_values("Fecha", kind="stable")

conteo = reviews.Fecha.value_counts()
assert len(conteo) == len(dias) and conteo.min() >= MIN_POR_DIA

reviews.to_csv("data/tripadvisor_reviews_fechadas.csv", index=False, date_format="%Y-%m-%d")
print(f"{len(reviews)} reseñas en {len(conteo)} días; mínimo {conteo.min()}, máximo {conteo.max()} por día")
