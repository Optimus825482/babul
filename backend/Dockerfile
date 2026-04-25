FROM python:3.12-slim

WORKDIR /app

# Sistem bağımlılıkları: curl_cffi + Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libcurl4-openssl-dev \
    libssl-dev \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium + sistem bağımlılıklarını kur
RUN playwright install chromium --with-deps

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    BROWSER_PROFILE_DIR=/app/data/browser-profile

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
