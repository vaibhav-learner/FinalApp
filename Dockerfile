# Use a slim Python image
FROM python:3.10-slim

# Set working directory to the root of your project
WORKDIR /code

# Install system dependencies required for Agent Framework
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt --pre

# Copy the entire project
COPY . /code/

# Expose port 8000 for Azure Container Apps
EXPOSE 8000

# Run Uvicorn pointing to the app folder's main.py
# Using 8000 as the port for Azure Container Apps compatibility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]