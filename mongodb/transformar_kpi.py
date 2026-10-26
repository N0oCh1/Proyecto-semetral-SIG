"""Transforma en MongoDB los datos cargados por scripts/cargar_mongodb.py en colecciones de KPI.

Ejecuta, en orden de nombre, cada pipeline de agregación de mongodb/pipelines/*.json. Cada archivo dice
de qué colección parte ("origen") y termina en $out, que reemplaza la colección de salida: se puede
volver a correr sin duplicar datos. Los pipelines también se pueden pegar en MongoDB Compass.

Ejecutar desde la raíz del repo: python mongodb/transformar_kpi.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
BASE = os.environ.get("MONGODB_DB", "agro_panama")
PIPELINES = Path("mongodb/pipelines")

if __name__ == "__main__":
    try:
        cliente = MongoClient(URI, serverSelectionTimeoutMS=5000)
        cliente.admin.command("ping")
        db = cliente[BASE]
        if not db.produccion_mensual.estimated_document_count():
            sys.exit("No hay datos en MongoDB. Corre antes scripts/cargar_mongodb.py")

        print(f"Base '{BASE}':")
        for ruta in sorted(PIPELINES.glob("*.json")):
            doc = json.loads(ruta.read_text(encoding="utf-8"))
            salida = doc["pipeline"][-1]["$out"]
            db[doc["origen"]].aggregate(doc["pipeline"])
            print(f"  {ruta.name}: {doc['origen']} -> {salida} ({db[salida].count_documents({})} documentos)")

        # Autochequeo: cada mes de producción encontró su clima y los totales no cambian al agregar
        assert db.kpi_mensual.count_documents({"lluvia_mm": None}) == 0, "meses de producción sin clima"
        ha = lambda col, campo: sum(d[campo] for d in db[col].find({}, {campo: 1}))
        assert abs(ha("produccion_mensual", "ha_cosechadas") - ha("kpi_cultivo", "ha")) < 1, "la superficie no cuadra"
    except PyMongoError as e:
        sys.exit(f"Error en MongoDB ({URI.split('@')[-1]}): {e}")
