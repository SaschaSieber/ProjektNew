FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Chrome and Chromedriver
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

# Install Google Chrome (hardcoded version)
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome.deb && \
    rm google-chrome.deb
    
# Install Chromedriver (matching version to Chrome)
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/131.0.6778.131/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Verify Google Chrome and Chromedriver installation
RUN google-chrome --version && chromedriver --version

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
