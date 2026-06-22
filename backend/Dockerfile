FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \    build-essential \    libpq-dev \    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files (if any)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Use gunicorn as the entry point
CMD ["gunicorn", "elo_terapeutico.wsgi:application", "--bind", "0.0.0.0:8000"]
