"""Copia las colecciones de KPI de MongoDB a PostgreSQL (esquema agro) para Power BI.

El cluster gratuito de Atlas no tiene Atlas SQL, así que Power BI lee de PostgreSQL con su conector nativo.
Cada tabla se reemplaza completa en cada corrida. Además crea agro.regiones con las coordenadas de
descargar_clima.LOCALIZACIONES, para el mapa.

Requiere PostgreSQL levantado (docker compose up -d) y POSTGRES_* en .env.
Ejecutar desde la raíz del repo: python scripts/exportar_postgres.py
"""
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from descargar_clima import LOCALIZACIONES

load_dotenv()

COLECCIONES = ["kpi_cultivo", "kpi_cultivo_region", "kpi_mensual", "clima_mensual"]
ESQUEMA = "agro"

if __name__ == "__main__":
    try:
        db = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
                         serverSelectionTimeoutMS=5000)[os.environ.get("MONGODB_DB", "agro_panama")]
        tablas = {c: pd.DataFrame(db[c].find({}, {"_id": 0})) for c in COLECCIONES}
    except PyMongoError as e:
        sys.exit(f"No se pudo leer MongoDB: {e}")
    if vacias := [c for c, df in tablas.items() if df.empty]:
        sys.exit(f"Colecciones vacías en MongoDB: {', '.join(vacias)}. Corre antes mongodb/transformar_kpi.py")
    tablas["regiones"] = pd.DataFrame(LOCALIZACIONES)

    url = URL.create("postgresql+psycopg",
                     username=os.environ.get("POSTGRES_USER", "sig"),
                     password=os.environ.get("POSTGRES_PASSWORD"),
                     host=os.environ.get("POSTGRES_HOST", "localhost"),
                     port=int(os.environ.get("POSTGRES_PORT", 5432)),
                     database=os.environ.get("POSTGRES_DB", "agro_panama"))
    try:
        with create_engine(url).begin() as con:  # una transacción: o se copian todas o ninguna
            con.execute(text(f"CREATE SCHEMA IF NOT EXISTS {ESQUEMA}"))
            for nombre, df in tablas.items():
                df.to_sql(nombre, con, schema=ESQUEMA, if_exists="replace", index=False)
                n = con.execute(text(f"SELECT count(*) FROM {ESQUEMA}.{nombre}")).scalar()
                assert n == len(df), (nombre, n, len(df))
                print(f"  {ESQUEMA}.{nombre}: {n} filas")
    except SQLAlchemyError as e:
        sys.exit(f"No se pudo escribir en PostgreSQL ({url.host}:{url.port}). ¿Está levantado? "
                 f"docker compose up -d\n{e}")
