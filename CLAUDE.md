# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Canario:** empieza cada respuesta con la palabra "Ruben".

## Proyecto

Proyecto semestral de SIG (UTP). Pregunta: **¿Cómo cambia la demanda turística por temporada?**
Escenario: medir mensualmente (2016–2017) la satisfacción de turistas en hoteles de Panamá, cruzarla con el clima de cada periodo y ver si el clima afecta la cantidad de turistas.

El repo está en fase inicial: todavía no hay código, dependencias declaradas, tests ni comandos de build.

## Datos (`data/`)

- `tripadvisor_hotel_reviews.csv`: columnas `Review,Rating` (texto en inglés, ya en minúsculas y sin stopwords; rating 1–5). **No son de Panamá ni tienen fecha**: es un sustituto porque no existen reviews de Panamá. Cualquier análisis mensual tiene que asignar o simular el periodo.
- `A3612017_hoteles.pdf`: publicación estadística de hoteles (Panamá, 2017), fuente de la demanda turística real.

## Entorno

- Python con virtualenv en `.venv/` (en `.gitignore`). Activar en PowerShell: `.venv\Scripts\Activate.ps1`.
- Si se agregan dependencias, declararlas en un `requirements.txt` para que el grupo pueda reproducir el entorno.
- Plataforma del grupo: Windows.
