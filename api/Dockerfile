FROM python:3.10-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev python3-dev

COPY api/requirements.txt .
COPY langgraph /langgraph

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e /langgraph

COPY api/ .

ENV PYTHONPATH=/langgraph/src:$PYTHONPATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
