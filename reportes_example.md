# Reportes sugeridos para el dashboard (Power BI)

Ejemplo de las páginas del dashboard que responden la pregunta *¿Cómo varían los costos y la productividad de los cultivos?* y apoyan las decisiones. Todas usan las tablas del esquema `agro` de PostgreSQL (ver `postgres/modelo_datos.md`).

## Página 1: Resumen ejecutivo

**Tabla:** `kpi_cultivo`

- **Tarjetas por cultivo:** rendimiento qq/ha, costo/qq, margen/qq y rentabilidad %.
- **Barras:** costo/qq contra precio/qq por cultivo. Muestra de un vistazo que solo el arroz queda por encima de su costo.
- **Anillo:** reparto de la superficie entre cultivos (el arroz ocupa el 74 %).

## Página 2: Comparación por región

**Tablas:** `kpi_cultivo_region` + `regiones`

- **Mapa:** burbujas en cada región, con el tamaño según las hectáreas y el color según la rentabilidad (verde o rojo). Filtro por cultivo.
- **Ranking:** barras horizontales de rendimiento o costo/qq por región. Muestra que Azuero (Herrera y Los Santos) va primero y Veraguas y Chiriquí al final.
- **Dispersión rendimiento contra costo/qq:** un punto por región. Muestra que a más rendimiento, menor costo por quintal, que es la conclusión central.

## Página 3: Punto de equilibrio (el más útil para decidir)

Son medidas DAX nuevas, sin tocar la base:

- **Rendimiento de equilibrio** = `costo_ha / precio_qq`. Es cuántos qq/ha hacen falta para no perder.
- **Precio de equilibrio** = `costo_qq`. Es el precio mínimo de venta.

Con los datos actuales esto da:

| Cultivo | Equilibrio | Mejor región | ¿La alcanza? |
|---|---|---|---|
| Arroz | ~93 qq/ha | 108 qq/ha (Los Santos) | ✅ en 7 de 8 regiones (todas menos Coclé) |
| Maíz | ~130 qq/ha | 108 qq/ha (Herrera) | ❌ ninguna región; necesita un precio de al menos 21 B/. |
| Café | ~24 qq/ha | 20,5 qq/ha (Chiriquí) | ❌ le faltan unos 4 qq/ha |

Esto convierte "el maíz pierde" en una recomendación concreta: subir el rendimiento a 130 qq/ha o vender por encima de 21 B/.

## Página 4: Simulador de escenarios

Con los parámetros *What-if* de Power BI se mueven controles deslizantes:

- **Precio del maíz:** de 15 a 18 B/. (el rango de mercado).
- **Precio del café:** ±30 %.
- **Variación del costo:** ±10 %, para simular, por ejemplo, una subida de los fertilizantes.

Al mover los controles se recalculan el margen y la rentabilidad por región. Responde directamente al punto 8 del enunciado ("evaluar los riesgos de las decisiones") y luce bien en la demo.

## Página 5: Clima

**Tablas:** `clima_mensual` + `kpi_cultivo_region`

- **Lluvia y temperatura mensual por región:** líneas sobre el año agrícola, con los meses de cosecha marcados.
- **Lluvia anual contra rendimiento por región:** dispersión, para mostrar con honestidad que no hay una relación clara con tan pocas regiones.
- **Calendario:** mapa de calor de días de lluvia por región y mes, útil para planificar la cosecha (en septiembre y octubre llueve casi todos los días).

## Página 6: Tendencia mensual (opcional)

**Tabla:** `kpi_mensual`

- Producción y costo por mes de cosecha y por cultivo, para ver cuándo se concentra el flujo de caja (arroz de septiembre a diciembre; maíz y café de diciembre a febrero).
- Es la página más débil, porque la variación mensual es sintética. Úsenla solo para mostrar la estacionalidad.

## Por dónde empezar

Las páginas 1, 2 y 3 bastan para responder la pregunta y dar recomendaciones. La 4 cubre la parte de riesgos y es la que más suma en originalidad.
