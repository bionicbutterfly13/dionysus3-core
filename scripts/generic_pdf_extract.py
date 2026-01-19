import argparse
import os
from pypdf import PdfReader

def extract_text(pdf_path, output_path):
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist.")
        return

    try:
        reader = PdfReader(pdf_path)
        with open(output_path, 'w') as f:
            for page in reader.pages:
                f.write(page.extract_text() + "\n\n")
        print(f"Successfully extracted {len(reader.pages)} pages to {output_path}")
    except Exception as e:
        print(f"Error extracting text: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from PDF')
    parser.add_argument('pdf_path', help='Path to source PDF')
    parser.add_argument('output_path', help='Path to output TXT file')
    args = parser.parse_args()
    
    extract_text(args.pdf_path, args.output_path)
