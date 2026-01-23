
import os
import argparse
from pypdf import PdfReader
import docx

# Configuration
STAGING_ROOT = "/app/data/ingest_staging"
OUTPUT_DIR = "specs/marketing_rhapsodies"

# Define Extraction Targets
TARGETS = [
    {
        "name": "03_mechanisms",
        "source_dir": os.path.join(STAGING_ROOT, "mechanisms"),
        "files": [
            "Mechanism Training Transcript PDF.pdf", 
            "Copy-Accelerator_-Unique-Mechanism_template.pdf",
            "Genesis Unique Mechanisms_11-14-22.pdf"
        ],
        "output_file": os.path.join(OUTPUT_DIR, "03_mechanisms.md"),
        "header": "# RMBC 2.0: Unique Mechanisms Source Code\n\nAuto-generated extract.\n\n"
    },
    {
        "name": "05_brief_20",
        "source_dir": os.path.join(STAGING_ROOT, "brief20"),
        "files": [
            "01-11 Classic RMBC Brief.docx",
            "01-12 The New Brief.docx",
            "02-21 Brief Generator_Claude Projects.docx"
        ],
        "output_file": os.path.join(OUTPUT_DIR, "05_brief_20.md"),
        "header": "# RMBC 2.0: The Brief 20 Source Code\n\nAuto-generated extract.\n\n"
    }
]

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

def extract_text_from_docx(docx_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n\n'.join(full_text)
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
        return None

def main():
    print(f"Starting RMBC Unified Extraction...")
    
    # Ensure output dir exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    for target in TARGETS:
        print(f"\n--- Processing Target: {target['name']} ---")
        compiled_content = target['header']
        
        for filename in target['files']:
            file_path = os.path.join(target['source_dir'], filename)
            
            if not os.path.exists(file_path):
                print(f"⚠️ Warning: File not found: {file_path}")
                continue
                
            print(f"Processing: {filename}...")
            
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            elif filename.lower().endswith('.docx'):
                text = extract_text_from_docx(file_path)
            else:
                print(f"Skipping unknown format: {filename}")
                continue
            
            if text:
                compiled_content += f"## Source: {filename}\n\n"
                compiled_content += "```text\n"
                compiled_content += text
                compiled_content += "\n```\n\n"
                compiled_content += "---\n\n"
                
        with open(target['output_file'], "w") as f:
            f.write(compiled_content)
            
        print(f"✅ Saved to: {target['output_file']}")

if __name__ == "__main__":
    main()
