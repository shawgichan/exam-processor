from app.utils.file_processor import PDFProcessor

class ExamProcessorService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        
    async def process_exam_file(self, filename: str) -> dict:
        temp_file_path = f"temp/{filename}"
        try:
            exam_data = await self.pdf_processor.process_pdf(temp_file_path)
            
            response = {
                "id": 1,  # Placeholder ID
                "document_path": filename,
                **exam_data
            }
            
            return response
        except Exception as e:
            raise Exception(f"Failed to process exam file: {str(e)}")