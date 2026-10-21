# Proyecto-semetral-SIG

# Integrante del grupo
- Ruben Feng
- Nohelanys Camaño
- Juan Morales
- Kevin Linares
- Calvin miro


# Tema elegido para el proyecto 

¿Cómo cambia la demanda turística por temporada?

# Ecenario

como empresa para medir la satisfaccion, se quiere medir la satisfaccion de los turista que viajan en Panama. en los diferenete periodo del 2016 - 2017 mensualemente y definir que tipo de clima hubo en ese momento y si el clima afecta a la cantidad de turista que haya.

## que contendra

se va a querer medir la satisfaccion de los turista en los hoteles en panama, como no hay datos de review en panama se usara un dataset con esos comentarios 

# Requisitos del proyecto final

Resumen de lo que pide el documento *Proyecto Final de Sistemas de Información Gerencial*. Marcar cada casilla cuando esté hecha.

**Objetivo:** alinear un proceso de negocio con nuevas tendencias tecnológicas para apoyar la toma de decisiones gerenciales, usando conceptos de Ingeniería de Datos. El problema se debe justificar a nivel local (Panamá) o internacional.

## Equipo y roles

- [ ] Asignar a cada integrante un rol dentro del sector turismo, con capacidad de tomar decisiones.
- [ ] El liderazgo lo ejerce el **Director(a) de Tecnología**.
- [ ] De 1 a 2 integrantes forman parte del equipo de TI.

## Requisitos tecnológicos

- [ ] Gestionar **al menos 3 tipos de datos distintos** en estructura y formato. Lo que ya se tiene:
  - Datos tabulares: estadística mensual de hoteles de Panamá (`data/hoteles_panama_2016_2017.csv`, extraída del PDF `A3612017_hoteles.pdf`).
  - Texto no estructurado: reseñas de hoteles (`data/tripadvisor_reviews_fechadas.csv`, fechas simuladas).
  - Clima por periodo (pendiente; por ejemplo, datos JSON de una API).
- [ ] Orquestación de procesos de datos.
- [ ] Integración con **AWS o MongoDB**.
- [ ] Inteligencia artificial generativa u otra técnica de IA (por ejemplo, análisis de sentimiento de las reseñas).
- [ ] Prácticas de automatización en el área de negocio.
- [ ] Dashboard con los principales indicadores del negocio.

## Componentes mínimos

1. [ ] **Problema gerencial:** describir qué decisión necesita mejorar la organización.
2. [ ] **Fuentes de datos:** datos abiertos, CSV, bases de datos o datos sintéticos **documentados**. Las reseñas no son de Panamá y sus fechas son simuladas; esto se debe declarar.
3. [ ] **Pipeline de datos:** extracción, limpieza, transformación y almacenamiento.
4. [ ] **Base de datos:** estructurar los datos con SQL u otra tecnología apropiada.
5. [ ] **Análisis gerencial:** KPI, tendencias y comparaciones (por ejemplo: ocupación, pernoctaciones, satisfacción promedio por mes y temporada, relación con el clima).
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
- Si se toma un repositorio de referencia (por ejemplo, *Tourism Analytics Dashboard*), verificar que esté disponible, revisar su README, comprobar que tenga datos y código ejecutable, e identificar su licencia.
- **El objetivo no es copiar un proyecto**, sino adaptar una solución al problema gerencial, construir el pipeline, definir indicadores y generar recomendaciones basadas en los resultados.