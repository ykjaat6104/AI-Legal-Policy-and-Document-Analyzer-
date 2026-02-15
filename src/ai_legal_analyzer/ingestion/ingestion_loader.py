import io
import logging
from typing import Union, BinaryIO

# logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("loader")

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

class DocumentLoader:
    # handles loading txt, pdf, docx
    
    @staticmethod
    def load(file_obj: Union[BinaryIO, bytes], filename: str) -> str:
        filename = filename.lower()
        
        # seekable file object 
        if isinstance(file_obj, bytes):
            file_obj = io.BytesIO(file_obj)
        
        if filename.endswith('.pdf'):
            return DocumentLoader._parse_pdf(file_obj)
        elif filename.endswith('.docx'):
            return DocumentLoader._parse_docx(file_obj)
        elif filename.endswith('.txt'):
            return DocumentLoader._parse_txt(file_obj)
        else:
            raise ValueError(f"unsupported format: {filename}")

    @staticmethod
    def _parse_txt(file_obj: BinaryIO) -> str:
        # handle text files
        try:
            content = file_obj.read()
            if isinstance(content, str): return content
            return content.decode('utf-8')
        except UnicodeDecodeError:
            file_obj.seek(0)
            return file_obj.read().decode('latin-1')

    @staticmethod
    def _parse_pdf(file_obj: BinaryIO) -> str:
        # extract pdf text
        if not pypdf: raise ImportError("pypdf missing")
        try:
            reader = pypdf.PdfReader(file_obj)
            return "\n".join([p.extract_text() or "" for p in reader.pages])
        except Exception as e:
            raise ValueError(f"pdf error: {e}")

    @staticmethod
    def _parse_docx(file_obj: BinaryIO) -> str:
        # extract docx text
        if not docx: raise ImportError("python-docx missing")
        try:
            doc = docx.Document(file_obj)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            raise ValueError(f"docx error: {e}")
