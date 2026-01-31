
from pypdf import PdfReader
import sys

def inspect_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        print(f"Number of Pages: {len(reader.pages)}")
        print("-" * 20)
        
        # Read first page
        page1 = reader.pages[0]
        text = page1.extract_text()
        print("--- Page 1 Text Preview ---")
        print(text[:1000]) # Print first 1000 chars
        print("-" * 20)
        
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    inspect_pdf("20251031-01-r707jyuusoku.pdf")
