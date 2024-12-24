import PyPDF2
import re
from typing import Dict, Any, List
import pdf2image
import pytesseract
from PIL import Image
import io
import os
import logging

class PDFProcessor:
    def __init__(self):
        self.text_extraction_methods = [
            self._extract_text_pypdf,
            self._extract_text_ocr
        ]
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Ensure temp directories exist
        os.makedirs("temp/images", exist_ok=True)

    async def process_pdf(self, file_path: str) -> dict:
        """
        Process PDF file and extract exam information using multiple methods.
        """
        try:
            full_text = None
            extraction_error = None
            
            for method in self.text_extraction_methods:
                try:
                    self.logger.debug(f"Trying extraction method: {method.__name__}")
                    full_text = method(file_path)
                    if full_text and len(full_text.strip()) > 0:
                        self.logger.debug(f"Extracted text length: {len(full_text)}")
                        self.logger.debug(f"First 500 characters: {full_text[:500]}")
                        break
                except Exception as e:
                    extraction_error = e
                    self.logger.error(f"Error in {method.__name__}: {str(e)}")
                    continue
            
            if not full_text:
                raise Exception(f"Failed to extract text from PDF: {extraction_error}")
            
            # Extract exam details
            exam_info = self._extract_exam_info(full_text)
            self.logger.debug(f"Extracted exam info: {exam_info}")
            
            # Extract questions
            questions = self._extract_question_mc(full_text)
            self.logger.debug(f"Extracted questions count: {len(questions)}")
            
            return {
                **exam_info,
                "total_questions": len(questions),
                "total_marks": float(len(questions)),
                "questions": questions
            }
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise

    def _extract_text_pypdf(self, file_path: str) -> str:
        """Extract text using PyPDF2 (for searchable PDFs)"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ' '.join(page.extract_text() for page in reader.pages)
            self.logger.debug(f"PyPDF2 extracted text length: {len(text)}")
            return text

    def _extract_text_ocr(self, file_path: str) -> str:
        """Extract text using OCR (for scanned PDFs)"""
        self.logger.debug("Starting OCR extraction")
        
        try:
            # Convert PDF to images with higher DPI for better OCR
            images = pdf2image.convert_from_path(file_path, dpi=300)
            self.logger.debug(f"Converted PDF to {len(images)} images")
            
            full_text = []
            
            # Process each page
            for i, image in enumerate(images):
                try:
                    # Convert image to grayscale for better OCR
                    gray_image = image.convert('L')
                    
                    # Save debug image
                    debug_image_path = os.path.join("temp", "images", f"page_{i}.png")
                    self.logger.debug(f"Saving debug image to: {debug_image_path}")
                    gray_image.save(debug_image_path)
                    
                    # Process image with both Arabic and English OCR
                    text = ""
                    for lang in ['eng', 'ara']:
                        try:
                            page_text = pytesseract.image_to_string(
                                gray_image, 
                                lang=lang,
                                config='--psm 6 --oem 3'
                            )
                            text += f"\n{page_text}"
                        except Exception as ocr_err:
                            self.logger.error(f"OCR error for language {lang} on page {i}: {str(ocr_err)}")
                    
                    text = text.strip()
                    self.logger.debug(f"OCR extracted text length for page {i}: {len(text)}")
                    
                    if text:  # Only add non-empty text
                        full_text.append(text)
                    
                except Exception as page_err:
                    self.logger.error(f"Error processing page {i}: {str(page_err)}")
                    continue  # Continue with next page if one fails
            
            if not full_text:
                raise Exception("No text could be extracted from any page")
            
            # Combine all text with page separators
            combined_text = '\n\n------ Page Break ------\n\n'.join(full_text)
            self.logger.debug(f"Total OCR text length: {len(combined_text)}")
            
            return combined_text
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            raise

    def _extract_question_mc(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions and organize them by exam parts"""
        questions = []
        current_part = None
        current_section = None
        marks = None
        
        # Split text into lines for better processing
        lines = text.split('\n')
        
        # Patterns for identifying parts and sections
        part_pattern = r'(?:PART|Part|SECTION)\s+(?:ONE|TWO|THREE|FOUR|[1-4]|[I-IV])'
        marks_pattern = r'\((\d+)\s*marks?\)'
        section_patterns = {
            'comprehension': r'(?:read|READ)\s+the\s+(?:following|FOLLOWING)\s+(?:passage|PASSAGE)',
            'short_answers': r'(?:short|SHORT)\s*(?:answer|ANSWER)',
            'true_false': r'(?:true|TRUE)\s+(?:or|OR)\s+(?:false|FALSE)',
            'mcq': r'(?:multiple|MULTIPLE)\s+(?:choice|CHOICE)|(?:circle|CIRCLE)\s+(?:the|THE)\s+(?:correct|CORRECT)',
            'composition': r'(?:composition|COMPOSITION)',
            'summary': r'(?:summary|SUMMARY)'
        }
        
        question_start_patterns = [
            r'^\s*\d+[\.\)]\s+',  # Numbered questions
            r'^\s*[A-Za-z][\.\)]\s+',  # Lettered questions
            r'(?:Answer|ANSWER)\s+the\s+following',  # Question prompts
        ]
        
        # Option patterns including Arabic letters
        option_patterns = [
            r'^(?:[a-eA-E]|[أ-ه])[\.|\-|\)]\s*(.+)',
            r'^(?:[0-9]+)[\.|\-|\)]\s*(.+)',
            r'^\s*(?:□|○|●)\s*(.+)'
        ]
        
        current_question = None
        current_options = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for part headers
            part_match = re.search(part_pattern, line)
            if part_match:
                current_part = line
                continue
                
            # Check for marks
            marks_match = re.search(marks_pattern, line)
            if marks_match:
                marks = float(marks_match.group(1))
                continue
                
            # Check for section headers
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section_name
                    continue
                    
            # Check if line starts a new question
            is_question = any(re.match(pattern, line) for pattern in question_start_patterns)
            if is_question:
                # Save previous question if exists
                if current_question:
                    questions.append({
                        "question_text": current_question,
                        "question_type": "multiple_choice" if current_options else "short_answer",
                        "marks": marks if marks else 1.0,
                        "is_mandatory": True,
                        "options": [{"option": chr(ord('a') + i), "text": opt} 
                                  for i, opt in enumerate(current_options)],
                        "part": current_part,
                        "section": current_section
                    })
                
                current_question = line
                current_options = []
                continue
                
            # Check for options
            for pattern in option_patterns:
                option_match = re.match(pattern, line)
                if option_match:
                    option_text = option_match.group(1).strip()
                    # Filter out handwritten answers (usually shorter and contain specific patterns)
                    if not self._is_handwritten_answer(option_text):
                        current_options.append(option_text)
                    break
        
        # Add the last question if exists
        if current_question:
            questions.append({
                "question_text": current_question,
                "question_type": "multiple_choice" if current_options else "short_answer",
                "marks": marks if marks else 1.0,
                "is_mandatory": True,
                "options": [{"option": chr(ord('a') + i), "text": opt} 
                          for i, opt in enumerate(current_options)],
                "part": current_part,
                "section": current_section
            })
        
        return questions
        
    def _is_handwritten_answer(self, text: str) -> bool:
        """Detect if text is likely a handwritten answer"""
        # Patterns that suggest handwritten answers
        handwritten_patterns = [
            r'^[A-Za-z]$',  # Single letter answers
            r'^\s*[√×✓]?\s*$',  # Check marks
            r'^[0-9]+$',  # Single numbers
            r'^\s*[\.]{3,}\s*$',  # Ellipsis or dotted lines
            r'^\s*_+\s*$',  # Underscores
            r'.*\(\s*✓\s*\).*',  # Circled answers
        ]
        
        return any(re.match(pattern, text) for pattern in handwritten_patterns)

    def _extract_exam_info(self, text: str) -> Dict[str, Any]:
        """Extract exam information with enhanced Arabic support"""
        # Enhanced patterns for Arabic text
        subject_patterns = [
            r'(?:Subject|المادة|مادة|موضوع)[\s:]+([^\n]+)',
            r'(?:Course|المقرر|مقرر)[\s:]+([^\n]+)',
            r'امتحان[^\n]*(?:مادة|في)\s+([^\n]+)',
            r'([^\n]+)(?:امتحان|اختبار)',
            r'Introduction to ([^\n]+)',
            r'مقدمة في ([^\n]+)'
        ]
        
        institution_patterns = [
            r'(?:Institution|الجامعة|المؤسسة|الكلية)[\s:]+([^\n]+)',
            r'^([^\n]+(?:University|College|الجامعة|الكلية))[^\n]*',
            r'(?:وزارة|كلية|جامعة)[^\n]+([^\n]+)'
        ]
        
        # Try each pattern
        subject_name = None
        for pattern in subject_patterns:
            self.logger.debug(f"Trying subject pattern: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                subject_name = match.group(1).strip()
                self.logger.debug(f"Found subject: {subject_name}")
                break
        
        institution = None
        for pattern in institution_patterns:
            self.logger.debug(f"Trying institution pattern: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                institution = match.group(1).strip()
                self.logger.debug(f"Found institution: {institution}")
                break
        
        # Extract exam type
        exam_type_patterns = [
            r'(?:Final|Midterm|Quiz|النهائي|النصفي|الاختبار)\s*(?:Exam|Test|الامتحان|اختبار)',
            r'امتحان\s*(?:نهائي|نصفي|فصلي)',
            r'اختبار\s*(?:نهائي|نصفي|فصلي)'
        ]
        
        exam_type = "Final Exam"  # default
        for pattern in exam_type_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                exam_type = match.group(0)
                self.logger.debug(f"Found exam type: {exam_type}")
                break
        
        # Add additional patterns for exam duration
        time_patterns = [
            r'(?:Time|Duration|الوقت|المدة)\s*:\s*(\d+)\s*(?:Hours?|Hrs?|ساعات?)',
            r'(\d+)\s*(?:Hours?|Hrs?|ساعات?)'
        ]
        
        duration = None
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                duration = int(match.group(1))
                self.logger.debug(f"Found duration: {duration} hours")
                break
        
        return {
            "subject": subject_name,
            "institution": institution,
            "exam_type": exam_type,
            "duration": duration,
        }
