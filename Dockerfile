FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements_cloud.txt .
RUN pip install --no-cache-dir -r requirements_cloud.txt

# Copy application code
COPY . .

# Set environment variables
ENV CLOUD_MODE=true
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "cloud_server.py"]
