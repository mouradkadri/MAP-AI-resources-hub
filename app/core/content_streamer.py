import os
import PyPDF2
import docx

class ContentStreamer:
    """
    Handles memory-efficient streaming of text from various file formats.
    """
    
    @staticmethod
    def stream_pdf(file_path):
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text: yield text
        except Exception as e:
            print(f"    ❌ Error reading PDF: {e}")

    @staticmethod
    def stream_docx(file_path):
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text: yield para.text + "\n"
        except Exception:
            yield ""

    @staticmethod
    def stream_txt(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(4000) 
                    if not chunk: break
                    yield chunk
        except Exception:
            yield ""

    @classmethod
    def generator(cls, file_path, ext, chunk_size=4000, overlap=500):
        buffer = ""
        iterator = None
        
        if ext == '.pdf': iterator = cls.stream_pdf(file_path)
        elif ext == '.docx': iterator = cls.stream_docx(file_path)
        elif ext == '.txt': iterator = cls.stream_txt(file_path)
        else: return

        for incoming_text in iterator:
            buffer += incoming_text
            while len(buffer) >= chunk_size:
                yield buffer[:chunk_size]
                buffer = buffer[chunk_size - overlap:]
        
        if len(buffer) > 100:
            yield buffer