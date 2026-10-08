# Portfolio demo image — SPEC-002. Not a production plant deployment.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src ./src
COPY app ./app
COPY docs ./docs
COPY models ./models
COPY reports ./reports
COPY data/raw/MANIFEST.json data/raw/README.md data/raw/AGENTS.md data/raw/SCOPE_STATE.json ./data/raw/

ENV PYTHONPATH=/app/src
EXPOSE 8501

# Runs in demo mode out of the box (derived artifacts in reports/demo).
# Optional: mount NASA C-MAPSS to enable the per-engine explanation tab:
#   docker run -p 8501:8501 -v /path/to/cmapss:/data/cmapss pm-survival
ENV PM_RAW_DIR=/data/cmapss

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
