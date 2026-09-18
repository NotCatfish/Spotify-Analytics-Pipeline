FROM python:3.11-slim

WORKDIR /app

COPY fastapi/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY models/ /app/models/
COPY data/processed/Engineered_Spotify_Portable.db /app/data/processed/Engineered_Spotify_Portable.db
COPY fastapi/ /app/fastapi/

EXPOSE 8000

WORKDIR /app/fastapi
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]