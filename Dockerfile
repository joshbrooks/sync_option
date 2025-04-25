# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS builder

# Set environment variables

# Set work directory
WORKDIR /app

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /usr/local/bin/uv

FROM builder AS sync
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=/usr/local/bin/python \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never
# Copy only dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

FROM builder AS final
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=/usr/local/bin/python \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# Copy virtual environment from sync stage
COPY --from=sync /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy project files
COPY . .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --group server

# Collect static files
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER nobody

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "testproject.wsgi:application"] 