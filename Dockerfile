# Use Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements and source code to the container
COPY requirements.txt ./
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8080

# Set the command to run the Flask app
CMD ["python", "app.py", "--port=8080"]
