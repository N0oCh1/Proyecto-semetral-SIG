# Proyecto-semetral-SIG

# Integrante del grupo
- Ruben Feng
- Nohelanys Camaño
- Juan Morales
- Kevin Linares
- Calvin miro


# Tema elegido para el proyecto 

Sector agropecuario: ¿Cómo varían los costos y la productividad de los cultivos?

# Escenario

Como empresa del sector agropecuario en Panamá, se quiere comparar los costos de producción y la productividad (rendimiento por hectárea) de **maíz, arroz y café** en el año agrícola 2025–2026, por región y por sistema de cultivo, cruzarlos con el clima de cada región y ver si el clima afecta a la productividad y al costo por quintal.

## Qué contendrá

- Tablas en PDF del MIDA, año agrícola 2025–2026 (`data/Documento_referencia/`):
  - `Proyecciones-de-Siembra-y-Cosecha-2025-2026.pdf`: productores, superficie, producción (qq) y rendimiento (qq/ha) por región y sistema de cultivo. Son **proyecciones**, no cosechas reales.
  - `Costo-normativo-maiz-2025-026.pdf`: costo por hectárea del maíz mecanizado y a chuzo con tecnología (y del sorgo, que no se usa).
  - `Costos-de-arroz-mecanizado-en-secano-2025-2026.pdf`: costo por hectárea, rendimiento y precio esperados del arroz en secano.
  - `Costo-normativo-cafe-2025-2026.pdf`: costo por hectárea del café robusta en sus primeros 5 años, solo y asociado con plátano.
- JSON por cultivo extraídos de los PDF con IA generativa: `python scripts/extraer_json_pdf.py` (LangChain + Gemini, requiere `GOOGLE_API_KEY`). Guarda en `data/semiestructurado/ia/` y compara con los JSON copiados a mano de `data/semiestructurado/`.
- Datos sintéticos mensuales del año agrícola 2025–2026 (`data/estructurado/produccion_mensual_2025_2026.csv`), generados con `python scripts/generar_datos_sinteticos.py` a partir de los JSON de `data/semiestructurado/`: hectáreas, rendimiento, producción, costos, precio y margen por región, cultivo y mes. La superficie anual es la del MIDA; el reparto mensual (calendario de cosecha) y la variación del rendimiento y del costo son simulados.
- Clima diario real de mayo 2025 a abril 2026 por región (`data/estructurado/clima_diario_2025_2026.csv`), descargado con `python scripts/descargar_clima.py` de la API de Open-Meteo: lluvia (mm y horas) y temperatura máxima, mínima y media. Un punto por región (la cabecera o sede regional, en `LOCALIZACIONES`).
- Base de datos MongoDB con todo lo anterior (`python scripts/cargar_mongodb.py`).

# Cómo ejecutar

Todos los comandos se corren en PowerShell desde la carpeta raíz del proyecto.

## 1. Preparar el entorno (solo la primera vez)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Si ya existe la carpeta `.venv`, saltar el primer comando.
- Si `Activate.ps1` da error de "ejecución de scripts deshabilitada", correr una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a activar.
- En las siguientes sesiones basta con activar el entorno: `.venv\Scripts\Activate.ps1` (la terminal muestra `(.venv)` al inicio).

## 2. Configurar la API key de Gemini (solo la primera vez)

1. Crear una API key en <https://aistudio.google.com/apikey>.
2. Copiar la plantilla: `Copy-Item .env.example .env`
3. Abrir `.env` y pegar la key en `GOOGLE_API_KEY=`.

El archivo `.env` no se sube a GitHub; cada integrante usa su propia key.

## Todo de una vez (pipeline)

Corre los pasos 3 a 7 en orden y se detiene si alguno falla:

```powershell
python scripts/pipeline.py           # todo
python scripts/pipeline.py --sin-ia  # sin llamar a Gemini: usa los JSON de ia/ que ya existen
```

## 3. Extraer los JSON de los PDF con IA

```powershell
python scripts/extraer_json_pdf.py          # los tres cultivos
python scripts/extraer_json_pdf.py cafe     # solo uno: arroz, maiz o cafe
```

- Entrada: los PDF de `data/Documento_referencia/`.
- Salida: `data/semiestructurado/ia/{arroz,maiz,cafe}.json`.
- El script muestra cuántos valores coinciden con los JSON copiados a mano y cuáles no. Si los rubros de costo no suman el total, no guarda ese JSON.
- Para que el paso 4 use los JSON de la IA, revisarlos y copiarlos de `data/semiestructurado/ia/` a `data/semiestructurado/`.

## 4. Generar los datos mensuales

```powershell
python scripts/generar_datos_sinteticos.py
```

- Entrada: `data/semiestructurado/*.json`.
- Salida: `data/estructurado/produccion_mensual_2025_2026.csv`.
- Usa una semilla fija: siempre genera el mismo archivo con los mismos JSON. No necesita API key ni internet.

## 5. Descargar el clima por región

```powershell
python scripts/descargar_clima.py
```

- Salida: `data/estructurado/clima_diario_2025_2026.csv` (365 días × 11 regiones).
- Necesita internet, pero no API key.

## 6. Cargar en MongoDB

```powershell
python scripts/cargar_mongodb.py                          # fichas de cultivo de la IA
python scripts/cargar_mongodb.py data/semiestructurado    # fichas copiadas a mano
```

- Configurar `MONGODB_URI` y `MONGODB_DB` en `.env` (ver `.env.example`). Por defecto usa MongoDB local (`mongodb://localhost:27017`, base `agro_panama`).
- Colecciones: `fichas_cultivo`, `produccion_mensual` y `clima_diario`. Se puede volver a correr: reemplaza la carga anterior.

## 7. Calcular los KPI en MongoDB

```powershell
python mongodb/transformar_kpi.py
```

Ejecuta en orden los pipelines de agregación de `mongodb/pipelines/` (cada uno se puede pegar en MongoDB Compass):

| Pipeline | Origen | Colección de salida |
|---|---|---|
| `01_clima_mensual.json` | `clima_diario` | `clima_mensual`: lluvia, días de lluvia y temperatura por región y mes |
| `02_kpi_mensual.json` | `produccion_mensual` | `kpi_mensual`: producción, costos y margen de cada mes con el clima de ese mes |
| `03_kpi_cultivo_region.json` | `produccion_mensual` | `kpi_cultivo_region`: rendimiento, costo/ha, costo/qq, margen y rentabilidad del año por cultivo y región, con el clima anual |
| `04_kpi_cultivo.json` | `produccion_mensual` | `kpi_cultivo`: los mismos KPI a nivel nacional por cultivo |

Los promedios se calculan con totales (p. ej. costo/qq = costo total / producción total), no promediando los meses. El maíz no tiene precio: su valor, margen y rentabilidad quedan en `null`.

# Requisitos del proyecto final

Resumen de lo que pide el documento *Proyecto Final de Sistemas de Información Gerencial*. Marcar cada casilla cuando esté hecha.

**Objetivo:** alinear un proceso de negocio con nuevas tendencias tecnológicas para apoyar la toma de decisiones gerenciales, usando conceptos de Ingeniería de Datos. El problema se debe justificar a nivel local (Panamá) o internacional.

## Equipo y roles

- [ ] Asignar a cada integrante un rol dentro del sector agropecuario, con capacidad de tomar decisiones.
- [ ] El liderazgo lo ejerce el **Director(a) de Tecnología**.
- [ ] De 1 a 2 integrantes forman parte del equipo de TI.

## Requisitos tecnológicos

- [ ] Gestionar **al menos 3 tipos de datos distintos** en estructura y formato. Lo que ya se tiene:
  - No estructurado: PDF del MIDA con las proyecciones y los costos (`data/Documento_referencia/`).
  - Semiestructurado: un JSON por cultivo con los valores de los PDF (`data/semiestructurado/`): costo por hectárea desglosado por rubro, análisis económico y superficie y rendimiento por región. Cada cultivo tiene su propia forma (el café trae el ciclo de 5 años; el maíz, otros sistemas).
  - Estructurado: CSV mensual generado a partir de los JSON (`data/estructurado/produccion_mensual_2025_2026.csv`) y CSV de clima diario por región (`data/estructurado/clima_diario_2025_2026.csv`).
- [ ] Orquestación de procesos de datos.
- [ ] Integración con **AWS o MongoDB**.
- [ ] Inteligencia artificial generativa u otra técnica de IA (por ejemplo, predecir el rendimiento de un cultivo según el clima).
- [ ] Prácticas de automatización en el área de negocio.
- [ ] Dashboard con los principales indicadores del negocio.

## Componentes mínimos

1. [ ] **Problema gerencial:** describir qué decisión necesita mejorar la organización.
2. [ ] **Fuentes de datos:** datos abiertos, CSV, bases de datos o datos sintéticos **documentados**. Si se usan datos sintéticos de cultivos, se debe declarar.
3. [ ] **Pipeline de datos:** extracción, limpieza, transformación y almacenamiento.
4. [ ] **Base de datos:** estructurar los datos con SQL u otra tecnología apropiada.
5. [ ] **Análisis gerencial:** KPI, tendencias y comparaciones (por ejemplo: rendimiento por hectárea, costo por hectárea, costo por quintal, margen por quintal, comparación por cultivo, región y sistema de cultivo, relación con el clima).
6. [ ] **Visualización:** dashboard interactivo en Power BI o herramienta equivalente.
7. [ ] **Recomendaciones:** interpretar los resultados y proponer decisiones basadas en evidencia.
8. [ ] **Riesgos:** evaluar los riesgos de las decisiones tomadas.

## Entregables

- [ ] Documento del proyecto final, con enlace a este repositorio de GitHub.
- [ ] Enlace de la presentación.

## Evaluación

**Documento escrito (35 %)**

| Criterio | Peso |
|---|---|
| Estructura, organización y redacción académica | 5 % |
| Planteamiento del problema, justificación y objetivos | 5 % |
| Fundamentación teórica y referencias bibliográficas | 5 % |
| Metodología y descripción de las fuentes de datos | 5 % |
| Diseño del sistema de información gerencial y proceso de datos | 5 % |
| Análisis de resultados, interpretación y recomendaciones gerenciales | 7 % |
| Conclusiones, limitaciones y trabajo futuro | 3 % |

**Desarrollo del proyecto tecnológico (40 %)**

| Criterio | Peso |
|---|---|
| Funcionalidad y cumplimiento de los objetivos | 8 % |
| Integración, calidad y preparación de los datos | 6 % |
| Diseño del flujo de datos (pipeline) | 6 % |
| Análisis, indicadores gerenciales y visualizaciones | 8 % |
| Utilidad para la toma de decisiones | 6 % |
| Originalidad, creatividad y valor agregado | 6 % |

**Presentación grupal (25 %)**

| Criterio | Peso |
|---|---|
| Organización y estructura de la presentación | 4 % |
| Claridad en la explicación del problema y la solución | 4 % |
| Demostración del funcionamiento del sistema | 6 % |
| Dominio del tema y participación equilibrada del equipo | 4 % |
| Creatividad, recursos visuales y comunicación | 3 % |
| Respuestas a preguntas y defensa de las decisiones | 4 % |

## Notas del documento

- Con datos reales de Panamá, priorizar fuentes abiertas y verificar sus condiciones de uso. Los datos sintéticos solo se permiten con fines académicos.
- Si se toma un repositorio de referencia (por ejemplo, *Agricultural Data Dashboard* o *Farm Analytics Dashboard*), verificar que esté disponible, revisar su README, comprobar que tenga datos y código ejecutable, e identificar su licencia.
- **El objetivo no es copiar un proyecto**, sino adaptar una solución al problema gerencial, construir el pipeline, definir indicadores y generar recomendaciones basadas en los resultados.