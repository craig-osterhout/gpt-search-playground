# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

#WORKDIR /usr/src/app/model
# Download model...huge file. Recommend download externally and copy in.
#RUN git lfs install && \
#  git clone https://huggingface.co/openlm-research/open_llama_3b_600bt_preview


WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

RUN python -c 'from sentence_transformers import SentenceTransformer; model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2"); model.save("/usr/src/app/models")'

COPY app.py .
COPY test.py .

ENTRYPOINT ["python", "test.py"]