SHELL := /bin/bash
PYTHON_VERSION := 3.11.5
PYENV_ROOT := $(HOME)/.pyenv
PYENV_BIN := $(PYENV_ROOT)/bin/pyenv
DOCKER_IMAGE_NAME := exam-processor
DOCKER_CONTAINER_NAME := exam-processor-container

ifeq ($(OS),Windows_NT)
	POETRY_PATH = %APPDATA%\Python\Scripts\poetry
else
	POETRY_PATH = $(HOME)/.local/bin/poetry
endif

.PHONY: install dev-up clean help install-pyenv configure-pyenv install-python clean-pyenv install-build-deps run docker-clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev-up       - Clean, rebuild, and run the Docker container"
	@echo "  make run          - Run existing Docker container (builds if needed)"
	@echo "  make docker-clean - Remove Docker container and image"
	@echo "  make clean        - Clean temporary files"
	@echo "  make clean-pyenv  - Remove existing pyenv installation"
	@echo "  make help         - Show this help message"

clean-pyenv:
	@echo "Cleaning existing pyenv installation..."
	@rm -rf $(PYENV_ROOT)

install-build-deps:
	@echo "Installing Python build dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y \
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
			python3-dev \
			python3-pip \
			python3-setuptools \
			libleptonica-dev \
			pkg-config; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install openssl readline sqlite3 xz zlib leptonica pkg-config; \
	else \
		echo "Please install Python build dependencies manually for your system"; \
	fi

install: clean-pyenv install-build-deps install-pyenv configure-pyenv install-python
	@echo "Installing dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install; \
	else \
		curl -sSL https://install.python-poetry.org | python3 -; \
		$(POETRY_PATH) install; \
	fi
	@echo "Installing system dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y \
			tesseract-ocr \
			tesseract-ocr-eng \
			tesseract-ocr-ara \
			poppler-utils \
			libleptonica-dev; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install tesseract tesseract-lang poppler leptonica; \
	else \
		echo "Please install Tesseract OCR and Poppler manually:"; \
		echo "Windows: https://github.com/UB-Mannheim/tesseract/wiki"; \
		echo "         Download Arabic language data from https://github.com/tesseract-ocr/tessdata"; \
		echo "Poppler: http://blog.alivate.com.au/poppler-windows/"; \
	fi

install-pyenv:
	@echo "Installing pyenv..."
	@curl https://pyenv.run | bash

configure-pyenv:
	@echo "Configuring pyenv..."
	@if ! grep -q 'export PYENV_ROOT' ~/.bashrc; then \
		echo 'export PYENV_ROOT="$$HOME/.pyenv"' >> ~/.bashrc; \
		echo '[[ -d $$PYENV_ROOT/bin ]] && export PATH="$$PYENV_ROOT/bin:$$PATH"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv init -)"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv virtualenv-init -)"' >> ~/.bashrc; \
	fi
	@PYENV_ROOT="$(HOME)/.pyenv" PATH="$(HOME)/.pyenv/bin:$(PATH)" eval "$(pyenv init -)"

install-python:
	@echo "Installing Python $(PYTHON_VERSION)..."
	@PYENV_ROOT="$(HOME)/.pyenv" PATH="$(HOME)/.pyenv/bin:$(PATH)" eval "$(pyenv init -)" && \
		$(PYENV_BIN) install --skip-existing $(PYTHON_VERSION)
	@PYENV_ROOT="$(HOME)/.pyenv" PATH="$(HOME)/.pyenv/bin:$(PATH)" eval "$(pyenv init -)" && \
		$(PYENV_BIN) local $(PYTHON_VERSION)
	@$(POETRY_PATH) config virtualenvs.prefer-active-python true

dev-up:
	@echo "Performing clean rebuild of Docker container..."
	-docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	-docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	-docker rmi $(DOCKER_IMAGE_NAME) 2>/dev/null || true
	docker build -t $(DOCKER_IMAGE_NAME) .
	docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8000:8000 -v $(PWD)/temp:/app/temp $(DOCKER_IMAGE_NAME)
	@echo "Container is running on http://localhost:8000"

run:
	@echo "Starting Docker container..."
	-docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	-docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	@if ! docker images $(DOCKER_IMAGE_NAME) | grep -q $(DOCKER_IMAGE_NAME); then \
		echo "Image not found, building..."; \
		docker build -t $(DOCKER_IMAGE_NAME) .; \
	fi
	docker run -d --name $(DOCKER_CONTAINER_NAME) -p 8000:8000 -v $(PWD)/temp:/app/temp $(DOCKER_IMAGE_NAME)
	@echo "Container is running on http://localhost:8000"

docker-clean:
	@echo "Cleaning Docker resources..."
	-docker stop $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	-docker rm $(DOCKER_CONTAINER_NAME) 2>/dev/null || true
	-docker rmi $(DOCKER_IMAGE_NAME) 2>/dev/null || true
	@echo "Docker cleanup complete"

clean:
	@echo "Cleaning temporary files..."
	rm -rf temp/
	mkdir -p temp/images
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete