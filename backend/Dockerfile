FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache --virtual .build-deps \
        build-base \
        python3-dev \
        libpq-dev \
        cairo-dev \
        gdk-pixbuf-dev \
        pango-dev \
        harfbuzz-dev \
        fribidi-dev \
        fontconfig-dev \
        libffi-dev \
        openssl-dev \
        cargo \
        rust \
    && apk add --no-cache \
        libpq \
        cairo \
        gdk-pixbuf \
        pango \
        harfbuzz \
        fribidi \
        fontconfig \
        libffi \
        openssl

WORKDIR /app

ARG REQUIREMENTS_FILE=requirements-prod.txt

COPY requirements*.txt ./

RUN python -m pip install --upgrade pip \
    && python -m pip install -r ${REQUIREMENTS_FILE} \
    && apk del .build-deps

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]