FROM python:3.11-slim

WORKDIR /app

COPY app/api/requirements.txt . 2>/dev/null || COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY models/ /app/models/
COPY data/processed/Engineered_Spotify_Portable.db /app/data/processed/Engineered_Spotify_Portable.db
COPY app/ /app/app/

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]