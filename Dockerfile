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

# Add Google Chrome's official signing key and repository
RUN wget -q -O /usr/share/keyrings/google-chrome.gpg https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable && apt-get clean

# Match ChromeDriver version to installed Chrome version
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) && \
    CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) && \
    wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
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
