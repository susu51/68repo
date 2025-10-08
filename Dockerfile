# Multi-stage Docker build for Kuryecini Platform

# Stage 1: Frontend Build
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY frontend/ .
RUN yarn build

# Stage 2: Backend Runtime
FROM python:3.11-slim AS backend-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend (serve as static files via FastAPI)
COPY --from=frontend-build /app/frontend/build ./frontend/build/

# Create uploads directory
RUN mkdir -p /app/backend/uploads

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]