# File: utils/processors.py
import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import magic
from skimage import exposure 

class ContentProcessor:
    def __init__(self):
        self.file_validator = magic.Magic(mime=True)
        
    def process_input(self, file_bytes, file_type):
        """Standardized content processor returning dict"""
        try:
            if file_type == 'application/pdf':
                result = self.process_pdf(file_bytes)
            elif file_type.startswith('image/'):
                result = self.process_image(file_bytes)
            elif file_type == 'text/plain':
                result = self.process_text(file_bytes)
            else:
                raise ValueError("Unsupported file type")
            
            # Standardize output format
            return {
                'text': result.get('text', ''),
                'pages': result.get('pages', []),
                'images': result.get('images', []),
                'metadata': {
                    'type': file_type,
                    'status': 'processed'
                }
            }
        except Exception as e:
            return {
                'text': '',
                'pages': [],
                'images': [],
                'metadata': {
                    'type': file_type,
                    'status': f'error: {str(e)}'
                }
            }
    
    def process_pdf(self, file_bytes):
        """Process PDF with standardized output"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        images = []
        
        for page in doc:
            # Text extraction with formatting
            text = page.get_text("text")
            pages_text.append(text)
            
            # Image extraction
            img_list = page.get_images()
            for img in img_list:
                base_img = doc.extract_image(img[0])
                images.append(self.enhance_image(base_img["image"]))
        
        return {
            'text': '\n'.join(pages_text),
            'pages': pages_text,
            'images': images
        }
    
    def process_image(self, file_bytes):
        """Improved image processing pipeline"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Enhanced preprocessing
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)  # Increased strength
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            contrast = clahe.apply(denoised)
            
            # OCR with multiple configurations
            custom_config = r'--oem 3 --psm 6 -l eng+equ'
            text = pytesseract.image_to_string(contrast, config=custom_config)
            
            return {
                'text': text,
                'pages': [text],
                'images': [contrast]
            }
        except Exception as e:
            raise ValueError(f"Image processing failed: {str(e)}")
    
    def process_text(self, file_bytes):
        """Process plain text files"""
        text = file_bytes.decode('utf-8')
        return {
            'text': text,
            'pages': [text],
            'images': []
        }
    
    def enhance_image(self, image_bytes):
        """Improved image enhancement"""
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('L')
        np_img = np.array(img)
        
        # Multiple enhancement techniques
        p2, p98 = np.percentile(np_img, (2, 98))
        img_rescale = exposure.rescale_intensity(np_img, in_range=(p2, p98))
        img_eq = exposure.equalize_hist(img_rescale)
        
        return Image.fromarray(img_eq)