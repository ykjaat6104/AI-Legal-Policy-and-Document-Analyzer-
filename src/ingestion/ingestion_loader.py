import io
import logging
from typing import Union, BinaryIO

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
    """Handles loading of TXT, PDF, and DOCX files into plain text."""

    @staticmethod
    def load(file_obj: Union[BinaryIO, bytes], filename: str) -> str:
        filename_lower = filename.lower()

        if isinstance(file_obj, bytes):
            file_obj = io.BytesIO(file_obj)

        if filename_lower.endswith('.pdf'):
            return DocumentLoader._parse_pdf(file_obj)
        elif filename_lower.endswith('.docx'):
            return DocumentLoader._parse_docx(file_obj)
        elif filename_lower.endswith('.txt'):
            return DocumentLoader._parse_txt(file_obj)
        else:
            raise ValueError(f"Unsupported file format: {filename}. Supported: TXT, PDF, DOCX")

    @staticmethod
    def _parse_txt(file_obj: BinaryIO) -> str:
        try:
            content = file_obj.read()
            if isinstance(content, str):
                return content
            return content.decode('utf-8')
        except UnicodeDecodeError:
            file_obj.seek(0)
            return file_obj.read().decode('latin-1')

    @staticmethod
    def _parse_pdf(file_obj: BinaryIO) -> str:
        if not pypdf:
            raise ImportError("pypdf is not installed. Run: pip install pypdf")
        try:
            reader = pypdf.PdfReader(file_obj)
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n".join(pages)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")

    @staticmethod
    def _parse_docx(file_obj: BinaryIO) -> str:
        if not docx:
            raise ImportError("python-docx is not installed. Run: pip install python-docx")
        try:
            doc = docx.Document(file_obj)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {e}")
