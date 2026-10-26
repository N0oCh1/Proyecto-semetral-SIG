# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Canario:** empieza cada respuesta con la palabra "Ruben".

## Proyecto

Proyecto semestral de SIG (UTP). Sector agropecuario. Pregunta: **¿Cómo varían los costos y la productividad de los cultivos?**
Escenario: comparar costos y productividad de **maíz, arroz y café** en el año agrícola 2025–2026, por región y sistema de cultivo, y cruzarlos con el clima de cada región.

El proyecto cambió de turismo a agropecuario; los datos de hoteles y reseñas se borraron (siguen en el historial de git, commit `aa01915`).
Todavía no hay tests ni comandos de build.

## Datos (`data/`)

- `Documento_referencia/*.pdf`: tablas del MIDA, año agrícola 2025–2026. Hay que extraerlas del PDF.
  - `Proyecciones-de-Siembra-y-Cosecha-2025-2026.pdf`: por región y sistema de cultivo (productores, ha, qq, qq/ha). Son proyecciones, no cosechas reales. Arroz (pág. 1), maíz (pág. 2), café (pág. 10, dentro de "industriales"); el resto de rubros no se usa.
  - `Costo-normativo-*.pdf` / `Costos-de-arroz-*.pdf`: costo por hectárea (B/.). El maíz tiene dos sistemas; el arroz solo secano (con precio esperado 27 B/./qq); el café es robusta, con costos por año de plantación (1–5) y precio de 170 B/./qq.
- `estructurado/produccion_mensual_2024_2025.csv`: **sintético**, lo genera `scripts/generar_datos_sinteticos.py` (semilla fija, ejecutar desde la raíz). Lee los valores base de `semiestructurado/*.json`; en el script solo queda el calendario de cosecha (`COSECHA`), que es un supuesto. El maíz no tiene precio (`precio_qq: null` → vacío en el CSV).
- `semiestructurado/{arroz,maiz,cafe}.json`: un documento por cultivo, copiado a mano de los PDF (`fuente` dice de qué página). El generador verifica que los rubros sumen `costo_ha.total`.
- `semiestructurado/ia/*.json`: los mismos documentos extraídos por `scripts/extraer_json_pdf.py` (LangChain + Gemini, salida estructurada con Pydantic, `GOOGLE_API_KEY`, modelo en `GEMINI_MODEL`). Qué página y qué sistema de cultivo usar de cada PDF está en `FICHAS`. No guarda un JSON si los rubros no suman el total, y lo compara con el JSON a mano. El generador lee `semiestructurado/*.json` (no `ia/`); para usar los de la IA hay que copiarlos un nivel arriba.
- `weather_URL_panama_2016_2017.py`: `obtener_clima()` descarga el clima diario de un solo punto (lat 9, lon -80) de la API de Open-Meteo y devuelve un DataFrame. Hay que pasarlo a 2025–2026 y a coordenadas por región.

## Entorno

- Python con virtualenv en `.venv/` (en `.gitignore`). Activar en PowerShell: `.venv\Scripts\Activate.ps1`.
- Si se agregan dependencias, declararlas en un `requirements.txt` para que el grupo pueda reproducir el entorno.
- Plataforma del grupo: Windows.
