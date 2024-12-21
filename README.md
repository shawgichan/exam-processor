# Exam Processor

A FastAPI application for processing and extracting information from exam documents (PDFs and scanned images).

## Prerequisites

Before running the application, make sure you have the following installed:

- Python 3.8 or higher
- Make (for running Makefile commands)

### System Dependencies

The application requires:

- Tesseract OCR (for processing scanned documents)
- Poppler (for PDF processing)

These will be installed automatically when running `make install` on Linux/macOS.

For Windows users:

1. Install Tesseract OCR: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install Poppler: Download from [blog.alivate.com.au/poppler-windows](http://blog.alivate.com.au/poppler-windows/)
3. Add both to your system PATH

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/shawgichan/exam-processor
cd exam-processor
```

2. Install dependencies:

```bash
make install
```

3. Start the development server:

```bash
make dev-up
```

The API will be available at: http://localhost:8000

API documentation (Swagger UI) will be available at: http://localhost:8000/docs

## Available Commands

- `make install` - Install all dependencies (including Poetry and system dependencies)
- `make dev-up` - Start the development server
- `make clean` - Clean temporary files and cache
- `make help` - Show available commands

## API Endpoints

### POST /api/v1/exam/upload

Upload and process an exam document (PDF or scanned image)

Example usage with curl:

```bash
curl -X POST "http://localhost:8000/api/v1/exam/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/exam.pdf"
```

## Project Structure

```
exam-processor/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── exam_processor.py
│   ├── schemas/
│   │   └── exam.py
│   ├── services/
│   │   └── exam_processor.py
│   └── utils/
│       └── file_processor.py
├── temp/
│   └── images/        # Temporary storage for OCR processing
├── Makefile
├── pyproject.toml
└── README.md
```

## Development

To contribute:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

## Troubleshooting

If you encounter issues:

1. Make sure all system dependencies are installed correctly
2. Check if the temp directory exists and has write permissions
3. For OCR issues, ensure Tesseract is installed and accessible
4. For PDF processing issues, ensure Poppler is installed correctly

For Windows users experiencing issues with Tesseract or Poppler:

1. Verify both are added to system PATH
2. Try reinstalling the dependencies
3. Check the Windows installation guides in the Prerequisites section
