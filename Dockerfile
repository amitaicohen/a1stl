FROM python:3.11-alpine

WORKDIR /app

# Copy application files
COPY election_server.py israel_elections_app.html ./

EXPOSE 8000

# Run standalone server
CMD ["python", "election_server.py", "8000"]
