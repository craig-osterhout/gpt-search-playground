# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

RUN python -c 'from sentence_transformers import SentenceTransformer; model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2"); model.save("/usr/src/app/models")'

COPY . .

ENTRYPOINT ["python", "create_embeddings.py"]