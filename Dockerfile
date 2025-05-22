# Use a slim Python base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for matplotlib, pandas, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

# Add label for GHCR provenance
LABEL org.opencontainers.image.source="https://github.com/suhailskhan/ai-usage-log"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Default command (can be overridden in ECS task definition)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
