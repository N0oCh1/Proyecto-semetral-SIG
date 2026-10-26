"""Genera datos sintéticos mensuales (año agrícola 2025-2026) de maíz, arroz y café por región de Panamá.

Base real (MIDA, año agrícola 2025-2026): los documentos JSON de data/semiestructurado/,
extraídos de los PDF de data/Documento_referencia/ (superficie y rendimiento por región, costo por
hectárea y precio por quintal).

Lo sintético: la superficie anual se reparte por mes según el calendario de cosecha, y el
rendimiento y el costo varían al azar alrededor de los valores del MIDA (semilla fija).

Ejecutar desde la raíz del repo: python scripts/generar_datos_sinteticos.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 2025
ANIO_AGRICOLA = 2025  # mayo 2025 - abril 2026
ENTRADA = Path("data/semiestructurado")
SALIDA = "data/estructurado/produccion_mensual_2025_2026.csv"

# Supuesto de la simulación (no viene de los PDF): parte de la cosecha anual que cae en cada mes
COSECHA = {
    "Arroz": {9: .15, 10: .30, 11: .35, 12: .20},
    "Maíz": {11: .10, 12: .40, 1: .35, 2: .15},
    "Café": {10: .05, 11: .20, 12: .30, 1: .30, 2: .15},
}


def cargar_cultivos():
    docs = {}
    for ruta in ENTRADA.glob("*.json"):
        doc = json.loads(ruta.read_text(encoding="utf-8"))
        r = doc["costo_ha"]["rubros"]
        suma = sum(v for k, v in r.items() if k != "recargos") + sum(r["recargos"].values())
        assert abs(suma - doc["costo_ha"]["total"]) < 0.05, f"{ruta.name}: los rubros no suman el total"
        docs[doc["cultivo"]] = doc
    assert docs.keys() == COSECHA.keys(), f"cultivos en JSON: {sorted(docs)}"
    return docs


def generar(docs):
    rng = np.random.default_rng(SEMILLA)
    filas = []
    for cultivo, calendario in COSECHA.items():
        doc = docs[cultivo]
        for r in doc["regiones"]:
            for mes, peso in calendario.items():
                anio = ANIO_AGRICOLA if mes >= 5 else ANIO_AGRICOLA + 1
                filas.append(dict(anio=anio, mes=mes, region=r["region"], cultivo=cultivo,
                                  sistema=doc["sistema"], ha_cosechadas=r["ha_cosechar"] * peso,
                                  rend_base=r["rendimiento_qq_ha"]))
    df = pd.DataFrame(filas)

    par = df.cultivo.map(docs)
    df["rendimiento_qq_ha"] = df.rend_base * rng.normal(1, 0.06, len(df))
    df["produccion_qq"] = df.ha_cosechadas * df.rendimiento_qq_ha

    # El costo del PDF está calculado para su rendimiento esperado; la parte por quintal cosechado
    # (cosecha y transporte) sube o baja con el rendimiento real, el resto es fijo por hectárea
    var_qq = par.map(lambda d: d["costo_ha"]["por_qq_cosechado"])
    fijo = par.map(lambda d: d["costo_ha"]["total"]
                   - d["costo_ha"]["por_qq_cosechado"] * d["analisis_economico"]["rendimiento_esperado_qq_ha"])
    # El costo se registra en el mes de cosecha; ±3 % de variación entre fincas y meses
    df["costo_ha"] = (fijo + var_qq * df.rendimiento_qq_ha) * rng.normal(1, 0.03, len(df))
    df["costo_total"] = df.costo_ha * df.ha_cosechadas
    df["costo_qq"] = df.costo_ha / df.rendimiento_qq_ha
    # precio_qq null en el JSON queda vacío en el CSV
    df["precio_qq"] = par.map(lambda d: d["analisis_economico"]["precio_qq"]).astype(float)
    df["valor_produccion"] = df.produccion_qq * df.precio_qq
    df["margen_qq"] = df.precio_qq - df.costo_qq
    df = df.round(2)
    df["fecha"] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    cols = ["fecha", "anio", "mes", "region", "cultivo", "sistema", "ha_cosechadas", "rendimiento_qq_ha",
            "produccion_qq", "costo_ha", "costo_total", "costo_qq", "precio_qq", "valor_produccion", "margen_qq"]
    return df[cols].sort_values(["fecha", "cultivo", "region"])


if __name__ == "__main__":
    docs = cargar_cultivos()
    df = generar(docs)

    # Autochequeo: el año agrícola reparte toda la superficie del MIDA y no hay huecos
    ha_mida = {(d["cultivo"], r["region"]): r["ha_cosechar"] for d in docs.values() for r in d["regiones"]}
    ha = df.groupby(["cultivo", "region"]).ha_cosechadas.sum()
    for (cultivo, region), total in ha.items():
        assert abs(total - ha_mida[cultivo, region]) < 0.1, (cultivo, region, total)
    assert df.drop(columns=["precio_qq", "valor_produccion", "margen_qq"]).notna().all().all()

    df.to_csv(SALIDA, index=False, date_format="%Y-%m-%d")

    resumen = df.groupby("cultivo").agg(ha=("ha_cosechadas", "sum"), qq=("produccion_qq", "sum"),
                                                  costo=("costo_total", "sum"))
    resumen["rend_qq_ha"] = resumen.qq / resumen.ha
    resumen["costo_qq"] = resumen.costo / resumen.qq
    print(f"{len(df)} filas -> {SALIDA}")
    print(resumen.round(1))
