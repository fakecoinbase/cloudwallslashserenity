FROM python:3.8-slim-buster

COPY $PWD/src /app
COPY $PWD/requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app"
