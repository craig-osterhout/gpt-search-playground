# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "create_embeddings.py"]