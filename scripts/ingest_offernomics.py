import PyPDF2
import sys

pdf_path = "/Volumes/Asylum/_Downloads/OfferNomics Digital Copy New (1) (2).pdf"
output_path = "offernomics_text.md"

try:
    print(f"Extracting textual DNA from: {pdf_path}")
    reader = PyPDF2.PdfReader(pdf_path)
    text = []
    
    # Metadata extraction for context
    if reader.metadata:
        text.append(f"# Metadata\n")
        for key, value in reader.metadata.items():
            text.append(f"- **{key}**: {value}")
        text.append("\n---\n")

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text.append(f"## Page {i+1}\n\n{page_text}\n\n")
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(text))
        
    print(f"Extraction complete. {len(reader.pages)} pages processed into {output_path}.")

except Exception as e:
    print(f"CRITICAL EXTRACTION FAILURE: {e}")
