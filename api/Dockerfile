FROM python:3.10-alpine
WORKDIR /app

RUN apt-get update --fix-missing \
    && apt-get install -y --no-install-recommends \
       gcc \
       build-essential \
       libmagic1 \
       poppler-utils \
       tesseract-ocr \
       libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY langgraph /langgraph

RUN pip install -e /langgraph

COPY api/ .

RUN apt-get purge -y --auto-remove gcc build-essential

ENV PYTHONPATH=/langgraph/src:$PYTHONPATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
