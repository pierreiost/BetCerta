FROM python:3.11-slim

# Install ffmpeg (required by MoviePy)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create output directory
RUN mkdir -p output

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
