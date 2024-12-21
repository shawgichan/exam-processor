# Use a multi-stage build for a smaller final image
FROM python:3.11.5-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    gcc \
    git \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install poetry and add to PATH
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./

# Configure poetry to create virtualenv in the project directory
RUN poetry config virtualenvs.in-project true

# Install dependencies
RUN poetry install --no-root --no-dev

# Copy the rest of the application
COPY . .

# Install the project itself
RUN poetry install --no-dev

# Final stage
FROM python:3.11.5-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy from builder
COPY --from=builder /app /app
COPY --from=builder /opt/poetry /opt/poetry

# Set environment variables
ENV PATH="/app/.venv/bin:/opt/poetry/bin:$PATH" \
    PYTHONPATH="/app:$PATH"

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "app.api.v1.endpoints.exam_processor:app", "--host", "0.0.0.0", "--port", "8000"]