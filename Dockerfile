FROM python:3.8-slim-buster

RUN apt update && apt install --yes gcc libpq-dev

COPY $PWD/src /app
COPY $PWD/requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app"
