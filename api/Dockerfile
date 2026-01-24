FROM python:3.9-slim 

WORKDIR /app

RUN apt-get clean \ 
    && rm -rf /var/lib/apt/lists/* \
    && apt-get update --fix-missing \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get purge -y --auto-remove gcc build-essential

COPY langgraph/ /langgraph/

RUN pip install -e /langgraph

COPY api/ .

COPY agents/ /app/agents/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
