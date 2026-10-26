# Modelo de datos (PostgreSQL, esquema `agro`)

Tablas que crea `scripts/exportar_postgres.py` a partir de MongoDB y que lee Power BI. Año agrícola 2025–2026, mercado nacional de Panamá. Unidades: qq = quintal (100 lb), B/. = balboas, ha = hectáreas.

Las claves (PK/FK) son lógicas: indican cómo relacionar las tablas en Power BI, pero la base no las impone.

```mermaid
erDiagram
    regiones ||--o{ produccion_mensual : region
    regiones ||--o{ kpi_mensual : region
    regiones ||--o{ clima_mensual : region
    regiones ||--o{ kpi_cultivo_region : region
    kpi_cultivo ||--o{ kpi_cultivo_region : cultivo

    regiones {
        text region PK "11 regiones del MIDA"
        text lugar "cabecera o sede regional"
        float8 lat
        float8 lon
    }

    produccion_mensual {
        timestamp fecha PK "primer día del mes"
        text cultivo PK
        text region PK,FK
        int8 anio
        int8 mes
        text sistema
        float8 ha_cosechadas
        float8 rendimiento_qq_ha
        float8 produccion_qq
        float8 costo_ha "B/. por ha"
        float8 costo_total "B/."
        float8 costo_qq "B/. por qq"
        float8 precio_qq "null si no hay precio"
        float8 valor_produccion
        float8 margen_qq
    }

    clima_mensual {
        text region PK,FK
        timestamp fecha PK
        int8 anio
        int8 mes
        float8 lluvia_mm
        float8 horas_lluvia
        int8 dias_lluvia "días con 1 mm o más"
        float8 temp_max_c
        float8 temp_min_c
        float8 temp_media_c
    }

    kpi_mensual {
        timestamp fecha PK
        text cultivo PK
        text region PK,FK
        int8 anio
        int8 mes
        text sistema
        float8 ha_cosechadas
        float8 rendimiento_qq_ha
        float8 produccion_qq
        float8 costo_ha
        float8 costo_total
        float8 costo_qq
        float8 precio_qq
        float8 valor_produccion
        float8 margen_qq
        float8 margen_total
        float8 lluvia_mm "clima del mismo mes"
        int8 dias_lluvia
        float8 temp_media_c
    }

    kpi_cultivo_region {
        text cultivo PK,FK
        text region PK,FK
        text sistema
        float8 ha
        float8 produccion_qq
        float8 rendimiento_qq_ha
        float8 costo_total
        float8 costo_ha
        float8 costo_qq
        float8 precio_qq
        float8 margen_qq
        float8 valor_produccion
        float8 margen_total
        float8 rentabilidad_pct "margen / costo x 100"
        float8 lluvia_anual_mm
        int8 dias_lluvia
        float8 temp_media_c
    }

    kpi_cultivo {
        text cultivo PK
        text sistema
        int8 num_regiones
        float8 ha
        float8 produccion_qq
        float8 rendimiento_qq_ha
        float8 costo_total
        float8 costo_ha
        float8 costo_qq
        float8 precio_qq
        float8 margen_qq
        float8 valor_produccion
        float8 margen_total
        float8 rentabilidad_pct
    }
```

## De dónde sale cada tabla

| Tabla | Origen en MongoDB | Granularidad |
|---|---|---|
| `regiones` | `LOCALIZACIONES` en `scripts/descargar_clima.py` | 1 fila por región |
| `produccion_mensual` | colección `produccion_mensual` (CSV sintético) | cultivo × región × mes |
| `clima_mensual` | `mongodb/pipelines/01_clima_mensual.json` | región × mes |
| `kpi_mensual` | `mongodb/pipelines/02_kpi_mensual.json` | cultivo × región × mes, con clima |
| `kpi_cultivo_region` | `mongodb/pipelines/03_kpi_cultivo_region.json` | cultivo × región (año agrícola) |
| `kpi_cultivo` | `mongodb/pipelines/04_kpi_cultivo.json` | cultivo (nacional) |

`kpi_mensual` ya incluye todas las columnas de `produccion_mensual`; en Power BI usar una de las dos para no duplicar totales.
