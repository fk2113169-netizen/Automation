FROM python:3.11-slim

WORKDIR /app

# Install minimal OS requirements for python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY . .

# Expose ports: 8501 for Streamlit and 8000 for FastAPI backend webhooks
EXPOSE 8501
EXPOSE 8000

# Start both services concurrently
# FastAPI starts in the background via uvicorn, followed by Streamlit in the foreground
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
