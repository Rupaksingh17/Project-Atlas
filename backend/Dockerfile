FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only runtime code and report corpus.
COPY backend/app ./backend/app

RUN useradd --system --uid 10001 --create-home atlas \
    && mkdir -p /app/backend/chroma_data \
    && chown -R atlas:atlas /home/atlas /app/backend/chroma_data
ENV HOME=/home/atlas PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER atlas

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
