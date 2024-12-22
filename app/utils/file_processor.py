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
        """Extract multiple choice questions and their options"""
        questions = []
        
        # More inclusive patterns for Arabic text
        question_patterns = [
            # English style numbering
            r'(?:(?:\d+|[١-٩]+)[\.|\-|\)]\s*)(.*?)(?=(?:\d+|[١-٩]+)[\.|\-|\)]|$)',
            # Arabic style numbering
            r'(?:(?:السؤال|سؤال)\s*(?:\d+|[١-٩]+)[:|\-|\)]\s*)(.*?)(?=(?:السؤال|سؤال)|$)',
            # General numbered lines
            r'^\s*(?:\d+|[١-٩]+)[\-|\)|\.](.+?)(?=^\s*(?:\d+|[١-٩]+)[\-|\)|\.]|\Z)'
        ]
        
        option_patterns = [
            # Multiple styles of option markers
            r'(?:[a-eA-E]|[أ-ه]|[ا-ى])[\.|\-|\)]\s*([^\n]+)',
            r'(?:□|○|●)\s*([^\n]+)',
            r'(?:\(\s*[a-eA-E]\s*\)|\{\s*[a-eA-E]\s*\})\s*([^\n]+)'
        ]
        
        # Try each question pattern
        for pattern in question_patterns:
            self.logger.debug(f"Trying question pattern: {pattern}")
            matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                q_content = match.group(1).strip()
                self.logger.debug(f"Found question: {q_content[:100]}...")
                
                # Try each option pattern
                options = []
                for opt_pattern in option_patterns:
                    opt_matches = re.findall(opt_pattern, q_content, re.MULTILINE)
                    if opt_matches:
                        self.logger.debug(f"Found options with pattern {opt_pattern}: {opt_matches}")
                        options.extend(opt_matches)
                
                if options:
                    questions.append({
                        "question_text": q_content.split('\n')[0].strip(),
                        "question_type": "multiple_choice",
                        "marks": 1.0,
                        "is_mandatory": True,
                        "options": [{"option": chr(ord('a') + i), "text": opt.strip()} 
                                  for i, opt in enumerate(options)]
                    })
        
        self.logger.debug(f"Total questions extracted: {len(questions)}")
        return questions

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
        
        return {
            "subject_name": subject_name or "Unknown Subject",
            "academic_year": None,
            "exam_type": exam_type,
            "semester": None,
            "institution": institution or "Unknown Institution"
        }