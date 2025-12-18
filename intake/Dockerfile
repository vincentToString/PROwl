FROM python:3.11-slim

ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install deps first for better caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy the actual package code
COPY . .

# Optional: your entrypoint (keep if you need runtime env validation)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

# IMPORTANT: no --reload on ECS
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
