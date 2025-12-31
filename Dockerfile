FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask plexapi gunicorn

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
