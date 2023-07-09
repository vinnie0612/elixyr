# Use the latest official Alpine-based Python base image
FROM python:3.10-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install libmagic for python-magic
RUN apk add libmagic

# Copy the Flask application code to the working directory
COPY . .

# Expose port 5000
EXPOSE 8081

# Set the entrypoint command to run the Flask application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8081", "app:app"]
