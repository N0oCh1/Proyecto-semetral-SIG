"""Ejecuta el pipeline completo, en orden, y se detiene en el primer paso que falle.

  1. Extracción con IA: PDF -> JSON por cultivo (data/semiestructurado/ia/)
  2. Transformación: JSON -> CSV mensual sintético (data/estructurado/)
  3. Extracción: clima diario por región desde Open-Meteo (data/estructurado/)
  4. Almacenamiento: todo a MongoDB
  5. Transformación en MongoDB: pipelines de agregación -> colecciones de KPI (mongodb/pipelines/)

Ejecutar desde la raíz del repo:
    python scripts/pipeline.py           # todo
    python scripts/pipeline.py --sin-ia  # sin llamar a Gemini: usa los JSON de ia/ que ya existen
"""
import subprocess
import sys
import time
from datetime import datetime

PASOS = [
    ("Extraer JSON de los PDF con IA", "scripts/extraer_json_pdf.py"),
    ("Generar producción mensual", "scripts/generar_datos_sinteticos.py"),
    ("Descargar clima por región", "scripts/descargar_clima.py"),
    ("Cargar en MongoDB", "scripts/cargar_mongodb.py"),
    ("Calcular KPI en MongoDB", "mongodb/transformar_kpi.py"),
]

if __name__ == "__main__":
    pasos = PASOS[1:] if "--sin-ia" in sys.argv else PASOS
    inicio = time.time()
    print(f"Pipeline iniciado {datetime.now():%Y-%m-%d %H:%M:%S}")
    for i, (nombre, script) in enumerate(pasos, 1):
        print(f"\n[{i}/{len(pasos)}] {nombre} ({script})", flush=True)
        t = time.time()
        # sys.executable: el mismo Python del .venv que corre el pipeline
        if subprocess.run([sys.executable, script]).returncode != 0:
            sys.exit(f"\nPipeline detenido: falló '{nombre}'. Los pasos siguientes no se ejecutaron.")
        print(f"   OK ({time.time() - t:.1f} s)")
    print(f"\nPipeline completo en {time.time() - inicio:.1f} s")
