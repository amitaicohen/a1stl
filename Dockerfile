
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY election_server.py .
COPY index.html .

EXPOSE 8000

CMD ["python", "election_server.py"]
