FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements and source code to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download de_core_news_md

# Expose the application port
EXPOSE 8080

# Set the command to run the Flask app
CMD ["python", "app.py", "--port=8080"]
