# Multi-stage Docker build optimized for uv
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Install uv - using the official installer for better reliability
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables for uv optimization
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache/
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Copy dependency files for caching (most specific to least specific)
COPY uv.lock* ./
COPY pyproject.toml ./
COPY README.md ./

# Create virtual environment and install dependencies
# Use --frozen if lock file exists, otherwise allow resolution
RUN --mount=type=cache,target=/opt/uv-cache/ \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-install-project; \
    else \
        uv sync --no-install-project; \
    fi

# Copy the project source code
COPY goldenverba ./goldenverba

# Install the project itself (non-editable for production)
RUN --mount=type=cache,target=/opt/uv-cache/ \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-editable; \
    else \
        uv sync --no-editable; \
    fi

# Stage 2: Production image
FROM python:3.11-slim AS production

# Install system dependencies needed at runtime
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Copy only the virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy the application source (needed for runtime)
COPY --from=builder --chown=app:app /app/goldenverba /app/goldenverba
COPY --from=builder --chown=app:app /app/pyproject.toml /app/pyproject.toml
COPY --from=builder --chown=app:app /app/README.md /app/README.md

# Set working directory and user
WORKDIR /app
USER app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Health check with proper error handling
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health', timeout=10)" || exit 1

EXPOSE 8080
CMD ["verba", "start", "--host", "0.0.0.0", "--port", "8080"]
