# Use Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy source code and requirements to the container
COPY . /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download the SpaCy language model
RUN python -m spacy download de_core_news_md

# Expose the application port
EXPOSE 8080

# Set the command to run the Flask app
CMD ["python", "app.py", "--port=8080"]
