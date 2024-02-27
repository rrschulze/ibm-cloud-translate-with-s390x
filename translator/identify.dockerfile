# syntax=docker/dockerfile:1
FROM python:3.10.9-slim

WORKDIR /translate

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://vsi-s390x-02:4318"
CMD [ "python3", "identify.py"]