from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from app.schemas.exam import ExamResponse
from app.services.exam_processor import ExamProcessorService
import shutil
import os

# Create FastAPI app instance
app = FastAPI(
    title="Exam Processor API",
    description="API for processing and extracting information from exam documents",
    version="1.0.0"
)

router = APIRouter(prefix="/exam", tags=["exam"])

@router.post("/upload", response_model=ExamResponse)
async def upload_exam(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are currently supported."
        )
    
    os.makedirs("temp", exist_ok=True)
    temp_file_path = f"temp/{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processor = ExamProcessorService()
        result = await processor.process_exam_file(file.filename)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# Add router to app
app.include_router(router, prefix="/api/v1")