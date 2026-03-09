# Build Stage for Frontend
FROM node:22-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_URL
ARG VITE_API_KEY
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_KEY=$VITE_API_KEY
RUN npm run build

# Runtime Stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Set up virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create necessary directories
RUN mkdir -p data

# Expose port for Render
EXPOSE 8000

# Run the application (uses PORT env var set by hosting platform)
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
