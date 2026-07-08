import pypdf
from io import BytesIO


def extract_text_from_pdf(file: BytesIO) -> str:
    """
    Extracts text from a PDF file and returns it as a list of strings, one for each page.
    """
    pdf_reader = pypdf.PdfReader(file)
    print(f"Total pages in PDF: {len(pdf_reader.pages)}")
    full_text = ""

    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            full_text += text
            full_text += "\n\n"  # Add a newline between pages for better readability

    
    return full_text


def chunk_text(text:str, chunk_size: int = 1000, chunk_overlap:int = 200) -> list[str]:
    """
    Splits the input text into chunks of specified size with optional overlap.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end]) 
        start += chunk_size - chunk_overlap
    return chunks
    