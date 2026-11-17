import os
from typing import List, Dict, Any
import pypdf
import docx
import pandas as pd
from pptx import Presentation
import markdown
from bs4 import BeautifulSoup

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text_from_csv(file_path: str) -> str:
    df = pd.read_csv(file_path)
    return df.to_string()

def extract_text_from_xlsx(file_path: str) -> str:
    df = pd.read_excel(file_path)
    return df.to_string()

def extract_text_from_pptx(file_path: str) -> str:
    prs = Presentation(file_path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

def extract_text_from_md(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext == ".csv":
        return extract_text_from_csv(file_path)
    elif ext in [".xlsx", ".xls"]:
        return extract_text_from_xlsx(file_path)
    elif ext == ".pptx":
        return extract_text_from_pptx(file_path)
    elif ext == ".md":
        return extract_text_from_md(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def clean_text(text: str) -> str:
    # Basic cleaning: remove extra whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)
