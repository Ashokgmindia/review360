FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Collect static files at build time
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "review360.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]


