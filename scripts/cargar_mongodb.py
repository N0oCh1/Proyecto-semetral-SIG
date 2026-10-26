"""Guarda en MongoDB los datos generados por el pipeline.

Colecciones:
  - fichas_cultivo: un documento por cultivo (los JSON de data/semiestructurado/ia/, extraídos por la IA).
  - produccion_mensual: una fila del CSV sintético por documento (data/estructurado/).
  - clima_diario: un día por región, del CSV de scripts/descargar_clima.py (data/estructurado/).

Conexión: MONGODB_URI y MONGODB_DB en .env (ver .env.example). Sirve igual para MongoDB local o Atlas.
Se puede volver a correr sin duplicar datos: cada carga reemplaza lo anterior.

Ejecutar desde la raíz del repo:
    python scripts/cargar_mongodb.py                              # JSON de la IA
    python scripts/cargar_mongodb.py data/semiestructurado        # JSON copiados a mano
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient, ReplaceOne
from pymongo.errors import PyMongoError

load_dotenv()

URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
BASE = os.environ.get("MONGODB_DB", "agro_panama")
CSV = Path("data/estructurado/produccion_mensual_2025_2026.csv")
CLIMA = Path("data/estructurado/clima_diario_2025_2026.csv")


def leer_fichas(carpeta):
    """Lee los JSON de cultivo y les agrega de dónde salieron y cuándo se cargaron."""
    ahora = datetime.now(timezone.utc)
    origen = "ia" if carpeta.name == "ia" else "manual"
    fichas = []
    for ruta in sorted(carpeta.glob("*.json")):
        doc = json.loads(ruta.read_text(encoding="utf-8"))
        doc.update(origen=origen, archivo=ruta.as_posix(), cargado_en=ahora)
        fichas.append(doc)
    return fichas


def leer_csv(ruta):
    df = pd.read_csv(ruta, parse_dates=["fecha"])
    # NaN (precio del maíz, días sin dato de clima) no es un valor válido en MongoDB: se guarda como null
    return df.astype(object).where(df.notna(), None).to_dict("records")


def cargar(db, fichas, produccion, clima):
    col = db.fichas_cultivo
    col.create_index([("cultivo", ASCENDING), ("anio_agricola", ASCENDING)], unique=True)
    # Reemplaza la ficha del mismo cultivo y año agrícola, o la crea si no existe
    col.bulk_write([ReplaceOne({"cultivo": f["cultivo"], "anio_agricola": f["anio_agricola"]}, f, upsert=True)
                    for f in fichas])

    col = db.produccion_mensual
    col.create_index([("cultivo", ASCENDING), ("region", ASCENDING), ("fecha", ASCENDING)], unique=True)
    # El CSV completo es la fuente: se borra la carga anterior y se inserta de nuevo
    col.delete_many({})
    col.insert_many(produccion)

    col = db.clima_diario
    col.create_index([("region", ASCENDING), ("fecha", ASCENDING)], unique=True)
    col.delete_many({})
    col.insert_many(clima)


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/semiestructurado/ia")
    fichas = leer_fichas(carpeta)
    if not fichas:
        sys.exit(f"No hay JSON en {carpeta}. Corre antes scripts/extraer_json_pdf.py")
    if not CSV.exists():
        sys.exit(f"No existe {CSV}. Corre antes scripts/generar_datos_sinteticos.py")
    if not CLIMA.exists():
        sys.exit(f"No existe {CLIMA}. Corre antes scripts/descargar_clima.py")
    produccion = leer_csv(CSV)
    clima = leer_csv(CLIMA)

    try:
        cliente = MongoClient(URI, serverSelectionTimeoutMS=5000)
        cliente.admin.command("ping")
        db = cliente[BASE]
        cargar(db, fichas, produccion, clima)
    except PyMongoError as e:
        sys.exit(f"No se pudo guardar en MongoDB ({URI.split('@')[-1]}): {e}")

    print(f"Base '{BASE}':")
    print(f"  fichas_cultivo: {db.fichas_cultivo.count_documents({})} documentos "
          f"({', '.join(f['cultivo'] for f in fichas)}; origen {fichas[0]['origen']})")
    print(f"  produccion_mensual: {db.produccion_mensual.count_documents({})} documentos")
    print(f"  clima_diario: {db.clima_diario.count_documents({})} documentos")
