FROM debian:trixie-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-fastapi python3-uvicorn python3-pydantic \
    && rm -rf /var/lib/apt/lists/*
COPY app ./app
EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
