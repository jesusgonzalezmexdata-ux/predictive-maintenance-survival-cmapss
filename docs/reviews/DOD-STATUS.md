# Definition of Done — estado tras SPEC-002 / TASK-008

Fecha: 2026-10-08

## A. Estadística y datos

| Pregunta | Antes | Ahora |
|----------|-------|-------|
| Dataset público + mapeo L2 | NO (faltaba taxonomía) | **SÍ** — C-MAPSS + [`docs/taxonomy.md`](../taxonomy.md) |
| Censura derecha | SÍ | SÍ |
| Prueba de supuestos | SÍ | SÍ |
| C-index / Brier | SÍ | SÍ |

## B. Negocio y comunicación

| Pregunta | Antes | Ahora |
|----------|-------|-------|
| ¿Cuándo conviene el preventivo? (fórmula) | PARCIAL (JSON) | **SÍ** — app Streamlit + \(t^*\) + mensaje de intervención |
| XAI por activo | NO | **SÍ** — contribuciones locales en lenguaje de riesgo (`explain.py`; no librería SHAP) |
| Lenguaje riesgo / costo / intervención | NO | **SÍ** en la app; model card técnico sigue existiendo para revisores |

## C. Herramientas y despliegue

| Pregunta | Antes | Ahora |
|----------|-------|-------|
| GitHub + README profesional + enlace vivo | NO | **PARCIAL** — README de portafolio listo; **sin remote ni URL pública** hasta que el owner publique |
| Despliegue nube HTTP | NO | **PARCIAL** — app + Dockerfile listos; URL pendiente de cuenta Cloud |
| Contenedor o requirements | PARCIAL | **SÍ** — `Dockerfile` + `requirements.txt` (numpy, pandas, lifelines, streamlit, plotly) |

## Veredicto

El cuestionario DoD **aún no es 100% SÍ** porque faltan dos acciones **solo del owner**:

1. Crear el repo en GitHub y hacer push.
2. Publicar en Streamlit Cloud / HF Spaces y pegar la URL en el README.

Todo lo demás del cuestionario queda cubierto en el árbol local.
