FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn surf_weather.main:app --host 0.0.0.0 --port ${PORT}"]
