import re
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_source) -> str:
    """
    Extracts and normalizes text from an uploaded PDF file or file path.
    Supports both Django UploadedFile objects (in-memory/temp) and string file paths.
    """
    text_chunks = []

    if isinstance(pdf_source, str):
        doc = fitz.open(pdf_source)
    else:
        # Reset pointer in case the file stream was already read
        pdf_source.seek(0)
        file_bytes = pdf_source.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pdf_source.seek(0)

    try:
        for page in doc:
            # "text" mode preserves natural reading order across standard layouts
            page_text = page.get_text("text")
            if page_text:
                text_chunks.append(page_text)
    finally:
        doc.close()

    raw_text = "\n".join(text_chunks)
    return clean_extracted_text(raw_text)


def clean_extracted_text(text: str) -> str:
    """
    Normalizes bullet symbols, excessive blank lines, and stray whitespace
    while keeping line breaks intact for section header detection.
    """
    # Normalize common bullet characters to a standard hyphen
    text = re.sub(r"[•●▪■◦▸►]", "-", text)
    # Collapse multiple spaces/tabs on the same line
    text = re.sub(r"[ \t]+", " ", text)
    # Strip trailing spaces per line and remove excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned