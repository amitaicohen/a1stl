
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -c "import firebase_admin; print('Firebase Admin import OK')"
COPY election_server.py .
COPY index.html .

EXPOSE 8000

CMD ["python", "election_server.py"]
