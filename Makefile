ifeq ($(OS),Windows_NT)
	POETRY_PATH = %APPDATA%\Python\Scripts\poetry
else
	POETRY_PATH = $(HOME)/.local/bin/poetry
endif

.PHONY: install dev-up clean help

help:
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make dev-up     - Start development server"
	@echo "  make clean      - Clean temporary files"
	@echo "  make help       - Show this help message"

install:
	@echo "Installing dependencies..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install; \
	else \
		curl -sSL https://install.python-poetry.org | python3 -; \
		$(POETRY_PATH) install; \
	fi
	@echo "Installing system dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install tesseract poppler; \
	else \
		echo "Please install Tesseract OCR and Poppler manually:"; \
		echo "Windows: https://github.com/UB-Mannheim/tesseract/wiki"; \
		echo "Poppler: http://blog.alivate.com.au/poppler-windows/"; \
	fi

dev-up:
	@echo "Starting development server..."
	poetry run uvicorn app.api.v1.endpoints.exam_processor:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "Cleaning temporary files..."
	rm -rf temp/
	mkdir -p temp/images
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete