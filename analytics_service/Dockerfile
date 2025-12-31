FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run both the consumer and api (simplified for demo, usually separate processes)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 & python worker.py"]
