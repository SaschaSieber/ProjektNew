FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for Chrome and ChromeDriver
RUN apt-get update -qq && apt-get install -y \
    wget \
    curl \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libgdk-pixbuf2.0-0 \
    libasound2 \
    fonts-liberation \
    libxss1 \
    xdg-utils && \
    apt-get clean

# Install Google Chrome (specific version)
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.198-1_amd64.deb && \
    apt-get install -y ./google-chrome.deb && \
    rm google-chrome.deb

# Install Chromedriver (specific version matching Chrome version)
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Copy application files and requirements to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download SpaCy language models
RUN python -m spacy download de_core_news_md && \
    python -m spacy download en_core_web_md

# Expose the application port
EXPOSE 8080

# Run the Flask application
CMD ["python", "app.py", "--port=8080"]
