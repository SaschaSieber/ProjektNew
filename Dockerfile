FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements and source code to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download de_core_news_md
RUN python -m spacy download en_core_web_md

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver-win64(1).zip chromedriver -d /usr/local/bin/

# Expose the application port
EXPOSE 8080

# Set the command to run the Flask app
CMD ["python", "app.py", "--port=8080"]
