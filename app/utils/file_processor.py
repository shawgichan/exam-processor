import PyPDF2
import re
from typing import Dict, Any, List

def extract_question_mc(text: str) -> List[Dict[str, Any]]:
    """Extract multiple choice questions and their options"""
    questions = []
    # Pattern for questions with numbers like "1.", "2.", etc.
    question_pattern = r'(\d+)\.\s*(.*?)(?=(?:\d+\.|$))'
    # Pattern for options like "a.", "b.", etc.
    option_pattern = r'([a-e])\.\s*([^\n]+)'
    
    # Find all questions
    matches = re.finditer(question_pattern, text, re.DOTALL)
    for match in matches:
        q_num, q_content = match.groups()
        q_text = q_content.strip()
        
        # Extract options for this question
        options = re.findall(option_pattern, q_text)
        
        if options:  # If it's a multiple choice question
            questions.append({
                "question_text": q_text.split('\n')[0].strip(),  # First line is the question
                "question_type": "multiple_choice",
                "marks": 1.0,  # Default mark
                "is_mandatory": True,
                "options": [{"option": opt[0], "text": opt[1].strip()} for opt in options]
            })
    
    return questions

async def process_pdf(file_path: str) -> dict:
    """
    Process PDF file and extract exam information using basic text extraction.
    """
    try:
        with open(file_path, 'rb') as file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()
            
            # Extract exam details
            exam_info = extract_exam_info(full_text)
            
            # Extract questions
            questions = extract_question_mc(full_text)
            
            return {
                **exam_info,
                "total_questions": len(questions),
                "total_marks": float(len(questions)),  # Assuming 1 mark per question
                "questions": questions
            }
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def extract_exam_info(text: str) -> Dict[str, Any]:
    """
    Extract exam information from text using pattern matching.
    """
    # Extract basic exam information
    institution_match = re.search(r'(.*?)\n', text)
    subject_match = re.search(r'Introduction to ([^\n]+)', text)
    exam_type_match = re.search(r'(Final Exam)', text)
    
    info = {
        "subject_name": subject_match.group(1) if subject_match else "Unknown Subject",
        "academic_year": None,  # Not specified in the document
        "exam_type": exam_type_match.group(1) if exam_type_match else "Final Exam",
        "semester": None,  # Not specified in the document
        "institution": institution_match.group(1) if institution_match else "Unknown Institution"
    }
    
    return info