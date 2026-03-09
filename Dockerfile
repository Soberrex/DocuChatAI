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

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Set up virtual environment to avoid system package conflicts
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies (torch removed - not used by any source code)

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create necessary directories
RUN mkdir -p chroma_db

# Expose port (Removed to let Railway manage routing via PORT env var)
# EXPOSE 8000 -> Caused routing mismatch (App on $PORT, LB on 8000)

# Health check (Let Railway handle this via TCP check)
# HEALTHCHECK removed to prevent conflict with dynamic PORT assignment

# Run the application
# Run on port 8000 hardcoded to match Railway's load balancer setting
CMD sh -c "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug --proxy-headers --forwarded-allow-ips '*'"
