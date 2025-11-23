# Stage 1: Build React UI
FROM node:18-alpine as build-step
WORKDIR /app
COPY ui_ux/package.json ui_ux/package-lock.json ./
# Install dependencies (legacy-peer-deps to avoid conflicts)
RUN npm install --legacy-peer-deps
COPY ui_ux/ ./
RUN npm run build

# Stage 2: Python Backend
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

# Copy built UI from Stage 1
COPY --from=build-step /app/build ./ui_ux/build

# Set environment variables
ENV CLOUD_MODE=true
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "cloud_server.py"]
