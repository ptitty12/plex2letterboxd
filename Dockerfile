FROM python:3.9-slim

WORKDIR /app

# Copy app files
COPY . /app

# Install runtime dependencies
RUN pip install --no-cache-dir flask plexapi

# Flask runs on 5000 by default
EXPOSE 5000

# Run the web app
CMD ["python", "app.py"]
