FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY deployment/requirements_cloud.txt .
RUN pip install --no-cache-dir -r requirements_cloud.txt

# Copy application code
COPY . .

# Build the UI (Assuming node is available or pre-built)
# For this Dockerfile, we assume ui_ux/build ALREADY EXISTS from the host
# If not, we would need a multi-stage build with Node.js

# Set environment variables
ENV CLOUD_MODE=true
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "deployment/cloud_server.py"]
