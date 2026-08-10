FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# System packages required by requirements.txt:
#   - build-essential, libpq-dev: building asyncpg / other C extensions
#   - tesseract-ocr, ghostscript, qpdf: ocrmypdf
#   - libgl1: transitive runtime dep of sentence-transformers/faster-whisper (torch stack)
# NOTE: this list has not been validated against a real `docker build` (no Docker
# daemon in the dev sandbox that authored this Dockerfile) - iterate on missing
# packages the first time this is actually built.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    ghostscript \
    qpdf \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
