# Use an official Python runtime as a parent image
# Python 3.10+ is recommended for Semantic Kernel
FROM python:3.11-slim

# Set environment variables
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# build-essential is often needed for some Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (8000 is standard for FastAPI/Uvicorn)
EXPOSE 8000

# Command to run the application
# Replace 'main:app' with your actual entry point (e.g., filename:app_instance)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]