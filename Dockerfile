# -----------------------------------------------------------
# QueueStorm Investigator – Docker image
# Uses a slim Python base; total image size < 500 MB.
# API keys are NEVER baked in – pass them at runtime via env.
# -----------------------------------------------------------
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY main.py models.py ai_engine.py ./

# Expose the API port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
