FROM python:3.11-slim

# Create venv outside app
ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /app

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies in one layer
RUN uv sync --frozen && \
    pip install --no-cache-dir \
    boto3 \
    jupyter \
    notebook \
    opensearch-py==2.7.1 \
    retrying==1.3.4

# Copy application code
COPY . /app/ai_service

# Default command runs the worker, but can be overridden
CMD ["python", "-m", "ai_service.worker"]