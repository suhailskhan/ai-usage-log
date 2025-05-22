FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/suhailskhan/ai-usage-log"
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app

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

COPY *.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# Default command (can be overridden in ECS task definition)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--global.developmentMode=false"]
