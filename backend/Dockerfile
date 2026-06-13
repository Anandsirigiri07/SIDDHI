# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system build dependencies (e.g. for bcrypt or other compiled dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code into /app/backend
COPY . /app/backend

# Copy the database file to the root of /app so sqlite:///./siddhi.db is found
COPY siddhi.db /app/siddhi.db

# Expose port 8000 for FastAPI
EXPOSE 8000

# Start Uvicorn server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
