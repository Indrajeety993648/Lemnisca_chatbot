FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF and faiss-cpu
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy application source
COPY backend/ /app/backend/
COPY .env.example /app/.env.example

# Create data directories
RUN mkdir -p /app/backend/data/pdfs \
             /app/backend/data/faiss_index \
             /app/backend/data/logs

ENV CLEARPATH_FAISS_INDEX_PATH=/app/backend/data/faiss_index
ENV CLEARPATH_PDF_DIR=/app/backend/data/pdfs
ENV CLEARPATH_LOG_FILE_PATH=/app/backend/data/logs/queries.jsonl

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
