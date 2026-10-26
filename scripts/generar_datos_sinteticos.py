"""Genera datos sintéticos mensuales (2024-2025) de maíz, arroz y café por región de Panamá.

Base real (MIDA, año agrícola 2025-2026, data/no_estructurado/):
  - Superficie a cosechar y rendimiento por región: Proyecciones-de-Siembra-y-Cosecha-2025-2026.pdf
  - Costo por hectárea y precio por quintal: Costo-normativo-*.pdf / Costos-de-arroz-*.pdf

Lo sintético: la superficie anual se reparte por mes según el calendario de cosecha, y el
rendimiento y el costo varían al azar alrededor de los valores del MIDA (semilla fija).

Ejecutar desde la raíz del repo: python scripts/generar_datos_sinteticos.py
"""
import numpy as np
import pandas as pd

SEMILLA = 2025
ANIOS = (2024, 2025)
SALIDA = "data/estructurado/produccion_mensual_2024_2025.csv"

# Por región: (hectáreas a cosechar, rendimiento qq/ha), proyección MIDA 2025-2026
SUPERFICIE = {
    "Arroz": {  # arroz mecanizado en secano, pág. 1
        "Chiriquí": (20500, 100.0), "Veraguas": (12060, 96.7), "Herrera": (2750, 105.0),
        "Coclé": (7897.1, 91.1), "Panamá Oeste": (270, 90.2), "Panamá Este": (18000, 105.0),
        "Los Santos": (11132, 105.0), "Darién": (11000, 100.0),
    },
    "Maíz": {  # maíz mecanizado, pág. 2
        "Chiriquí": (500, 75.0), "Veraguas": (74.4, 75.0), "Herrera": (2000, 106.0),
        "Los Santos": (15000, 115.0), "Darién": (35, 79.9),
    },
    "Café": {  # café, pág. 10
        "Chiriquí": (7714, 19.9), "Veraguas": (698, 4.5), "Herrera": (50, 10.0),
        "Coclé": (152, 13.6), "Panamá Oeste": (89, 8.0), "Colón": (1700, 12.0),
        "Panamá Este": (425, 9.6), "Bocas del Toro": (19, 10.0), "Darién": (625, 11.9),
        "Comarca Ngäbe Buglé": (399, 8.0),
    },
}

# costo_ref: costo total por ha del PDF; rend_ref: rendimiento con el que el PDF calcula ese costo;
# var_qq: parte del costo que crece por quintal cosechado (cosecha y transporte de la cosecha)
CULTIVOS = {
    "Arroz": dict(sistema="Mecanizado en secano", costo_ref=2508.01, rend_ref=105, var_qq=1.25,
                  precio_qq=27.0, cosecha={9: .15, 10: .30, 11: .35, 12: .20}),
    # shortcut: el PDF del maíz no trae precio; llenar precio_qq cuando tengan el precio de referencia
    "Maíz": dict(sistema="Mecanizado", costo_ref=2250.06, rend_ref=113, var_qq=1.00,
                 precio_qq=np.nan, cosecha={11: .10, 12: .40, 1: .35, 2: .15}),
    # Café robusta tecnificado, año 5 (plantación madura). Cosecha 2,700 + transporte 300 B/. para 70 qq
    "Café": dict(sistema="Tecnificado (robusta, año 5)", costo_ref=6476.19, rend_ref=70, var_qq=3000 / 70,
                 precio_qq=170.0, cosecha={10: .05, 11: .20, 12: .30, 1: .30, 2: .15}),
}


def generar():
    rng = np.random.default_rng(SEMILLA)
    filas = []
    for cultivo, c in CULTIVOS.items():
        for region, (ha_anual, rend_base) in SUPERFICIE[cultivo].items():
            for anio in ANIOS:
                for mes, peso in c["cosecha"].items():
                    filas.append(dict(anio=anio, mes=mes, region=region, cultivo=cultivo,
                                      sistema=c["sistema"], ha_cosechadas=ha_anual * peso,
                                      rend_base=rend_base))
    df = pd.DataFrame(filas)

    par = df.cultivo.map(CULTIVOS)
    df["rendimiento_qq_ha"] = df.rend_base * rng.normal(1, 0.06, len(df))
    df["produccion_qq"] = df.ha_cosechadas * df.rendimiento_qq_ha

    var_qq = par.map(lambda c: c["var_qq"])
    fijo = par.map(lambda c: c["costo_ref"] - c["var_qq"] * c["rend_ref"])
    # El costo se registra en el mes de cosecha; ±3 % de variación entre fincas y meses
    df["costo_ha"] = (fijo + var_qq * df.rendimiento_qq_ha) * rng.normal(1, 0.03, len(df))
    df["costo_total"] = df.costo_ha * df.ha_cosechadas
    df["costo_qq"] = df.costo_ha / df.rendimiento_qq_ha
    df["precio_qq"] = par.map(lambda c: c["precio_qq"])
    df["valor_produccion"] = df.produccion_qq * df.precio_qq
    df["margen_qq"] = df.precio_qq - df.costo_qq
    df = df.round(2)
    df["fecha"] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    cols = ["fecha", "anio", "mes", "region", "cultivo", "sistema", "ha_cosechadas", "rendimiento_qq_ha",
            "produccion_qq", "costo_ha", "costo_total", "costo_qq", "precio_qq", "valor_produccion", "margen_qq"]
    return df[cols].sort_values(["fecha", "cultivo", "region"])


if __name__ == "__main__":
    df = generar()

    # Autochequeo: cada año reparte toda la superficie del MIDA y no hay huecos
    ha = df.groupby(["cultivo", "region", "anio"]).ha_cosechadas.sum()
    for (cultivo, region, _), total in ha.items():
        assert abs(total - SUPERFICIE[cultivo][region][0]) < 0.1, (cultivo, region, total)
    assert df.drop(columns=["precio_qq", "valor_produccion", "margen_qq"]).notna().all().all()

    df.to_csv(SALIDA, index=False, date_format="%Y-%m-%d")

    resumen = df.groupby(["cultivo", "anio"]).agg(ha=("ha_cosechadas", "sum"), qq=("produccion_qq", "sum"),
                                                  costo=("costo_total", "sum"))
    resumen["rend_qq_ha"] = resumen.qq / resumen.ha
    resumen["costo_qq"] = resumen.costo / resumen.qq
    print(f"{len(df)} filas -> {SALIDA}")
    print(resumen.round(1))
