# Exam Processor

A FastAPI application for processing and extracting information from exam documents (PDFs and scanned images).

## Quick Start with Docker

1. Clone the repository:
```bash
git clone https://github.com/shawgichan/exam-processor
cd exam-processor
```

2. Build and run the application:
```bash
make dev-up
```

The API will be available at: http://localhost:8000  
API documentation (Swagger UI) will be available at: http://localhost:8000/docs

## Available Commands

- `make dev-up` - Clean, rebuild, and start the Docker container (use during development)
- `make run` - Start the Docker container (builds image if needed)
- `make clean` - Clean temporary files and cache
- `make help` - Show available commands

## Alternative: Local Development Setup

### Prerequisites

Before running the application locally, make sure you have the following installed:
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

### Local Installation

1. Install dependencies:
```bash
make install
```

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
├── Dockerfile
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

### Docker Issues
1. If the container fails to start:
   - Check Docker logs: `docker logs exam-processor-container`
   - Ensure ports are not in use: `lsof -i :8000`
   - Try rebuilding from scratch: `make dev-up`

2. If the build fails:
   - Ensure Docker daemon is running
   - Check available disk space
   - Try cleaning Docker system: `docker system prune`

### Local Development Issues
1. Make sure all system dependencies are installed correctly
2. Check if the temp directory exists and has write permissions
3. For OCR issues, ensure Tesseract is installed and accessible
4. For PDF processing issues, ensure Poppler is installed correctly

For Windows users experiencing issues with Tesseract or Poppler:
1. Verify both are added to system PATH
2. Try reinstalling the dependencies
3. Check the Windows installation guides in the Prerequisites section
