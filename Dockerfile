FROM python:3.11-slim

# Install system dependencies (untuk pycairo yang dibutuhkan xhtml2pdf)
RUN apt-get update && apt-get install -y \
    gcc \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh project
COPY . .

# Buat folder exports dan qrcodes jika belum ada
RUN mkdir -p exports app/static/qrcodes

ENV PORT=8000

EXPOSE 8000

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
