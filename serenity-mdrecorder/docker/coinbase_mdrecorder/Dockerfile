FROM python:3.7-slim-buster

COPY $PWD/src /app
COPY $PWD/requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app"
CMD ["python", "cloudwall/serenity/mdrecorder/coinbase.py"]