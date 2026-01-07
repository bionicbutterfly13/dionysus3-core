import PyPDF2
import sys
import os

pdf_path = "/Volumes/Asylum/_Downloads/mental-models-and-their-dynamics-adaptation-and-control.pdf"
output_path = "/Volumes/Asylum/dev/dionysus3-core/specs/treur_book_excerpts.txt"

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found")
    sys.exit(1)

try:
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        pages_to_extract = range(57, 74) # Pages 58-74 (0-indexed 57 to 73)
        
        with open(output_path, 'w') as out_file:
            for page_num in pages_to_extract:
                if page_num < len(reader.pages):
                    text = reader.pages[page_num].extract_text()
                    out_file.write(f"--- PAGE {page_num + 1} ---\n")
                    out_file.write(text)
                    out_file.write("\n\n")
        print(f"Successfully extracted text to {output_path}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
