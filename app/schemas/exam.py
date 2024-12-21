from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QuestionOption(BaseModel):
    option: str
    text: str

class QuestionBase(BaseModel):
    question_text: str
    question_type: str
    marks: float
    is_mandatory: bool = True
    options: Optional[List[QuestionOption]] = None

class ExamCreate(BaseModel):
    subject_name: str
    academic_year: Optional[int]
    total_questions: int
    total_marks: float
    exam_type: Optional[str]
    semester: Optional[str]
    institution: Optional[str]
    questions: List[QuestionBase]

class ExamResponse(ExamCreate):
    id: int
    document_path: str
    
    class Config:
        from_attributes = True