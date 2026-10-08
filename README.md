# Mantenimiento predictivo con supervivencia (NASA C-MAPSS)

**Pregunta de negocio:** ¿cuándo conviene el mantenimiento preventivo frente a dejar fallar el activo?

Este repositorio responde con un baseline gobernado de **análisis de supervivencia** (Weibull + Cox / Weibull AFT) sobre el dataset público **NASA C-MAPSS FD001**, una **política de costo** \(C(t)\) que entrega el tiempo óptimo de intervención \(t^*\), y una **app interactiva** en lenguaje de riesgo / costo / intervención.

> Evidencia de portafolio. **No** es un sistema de producción ni una certificación aeronáutica.

## Resultados (FD001, ventana temprana — sin filtrar el futuro)

| Señal | Valor |
|-------|------:|
| Régimen Weibull | β ≈ 4.60 → wear-out |
| Modelo elegido | Weibull AFT (PH de Cox no se sostiene en features tempranas) |
| C-index (validación) | ≈ 0.67 |
| Concordancia vs RUL (test censurado) | ≈ 0.46 (señal temprana débil; documentado) |
| \(t^*\) con \(C_f/C_p = 10\) | ≈ 105 ciclos |

Antes, pendientes sobre **toda** la trayectoria daban C-index ≈ 0.78 y ranking vs RUL ≈ 0.82. Eso filtraba información del futuro. Se corrigió a conciencia (TASK-007): el número bajó; el claim es más honesto.

## Qué incluye

- Censura por la derecha explícita (falla observada vs activo que sigue operando).
- Test de riesgos proporcionales (Schoenfeld) + fallback a Weibull AFT.
- Métricas de supervivencia: C-index e Integrated Brier Score (no Accuracy/F1).
- Fórmula de costo esperado por unidad de tiempo y \(t^* = \arg\min C(t)\).
- Taxonomía L2 ↔ sensores C-MAPSS: [`docs/taxonomy.md`](docs/taxonomy.md).
- Explicabilidad local por activo (contribuciones al riesgo, lenguaje de negocio).
- App Streamlit + Dockerfile.
- Gobernanza MDA (`repoctl`, specs, tasks, model card).

## Cómo ejecutar

### 1. Entorno

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Datos (no van en git)

Descarga el dataset NASA C-MAPSS y extrae solo los `.txt`:

```bash
python -m pm_survival extract --archive ruta\a\CMAPSSData.zip --out data/raw/cmapss
```

### 3. Evidencia offline

```bash
python -m pm_survival run --raw-dir data/raw/cmapss
```

Artefactos: `reports/eval_FD001.md`, `models/MODEL_CARD_FD001.md`.

### 4. App de decisión

```bash
streamlit run app/streamlit_app.py
```

Ajusta \(C_p\) y \(C_f\) en la barra lateral. La app responde **cuándo conviene el preventivo** y muestra los impulsores de riesgo del activo seleccionado.

### 5. Docker

```bash
docker build -t pm-survival .
docker run -p 8501:8501 -v /ruta/local/cmapss:/data/cmapss pm-survival
```

Abre `http://localhost:8501`.

## Enlace en vivo

**Pendiente de publicación por el owner** (Streamlit Community Cloud o Hugging Face Spaces).

Pasos sugeridos (Streamlit Cloud):

1. Sube este repositorio a GitHub.
2. En [share.streamlit.io](https://share.streamlit.io) → New app → este repo → `app/streamlit_app.py`.
3. Añade los datos C-MAPSS como secretos/archivos privados del Space **o** documenta que el visitante debe aportar la ruta (el dataset no se redistribuye desde este repo por política DEC-004).

Cuando exista la URL, reemplaza esta sección por el enlace HTTP.

## Metodología (resumen)

1. Evento = fin de trayectoria run-to-failure; test truncado = censura a la derecha.
2. Covariables = medias y pendientes en los **primeros 20 ciclos** solamente.
3. Weibull incondicional → régimen de falla + \(R(t)\) para la política de costo.
4. Cox PH si el supuesto se sostiene; si no, Weibull AFT.
5. \(C(t) = [C_p R(t) + C_f (1-R(t))] / \int_0^t R(x)\,dx\).

Detalle: [`docs/specs/SPEC-001-cmapss-survival-baseline.md`](docs/specs/SPEC-001-cmapss-survival-baseline.md), [`docs/specs/SPEC-002-dod-closure.md`](docs/specs/SPEC-002-dod-closure.md).

## Estructura

```text
src/pm_survival/   # pipeline, modelos, costo, explain, CLI
app/               # Streamlit
docs/taxonomy.md   # L2 ↔ C-MAPSS
reports/           # evidencia
models/            # model card
test/product/      # tests offline
```

## Licencia de datos

NASA C-MAPSS es un dataset público de referencia. Este repo **no** redistribuye los binarios/txt grandes (`.gitignore`). Obténlos de la fuente oficial.

---

Kernel de gobernanza multiagente: ver [`docs/KERNEL_README.md`](docs/KERNEL_README.md).
