
import pdfplumber
import pandas as pd

def inspect_table(file_path):
    with pdfplumber.open(file_path) as pdf:
        print(f"Total Pages: {len(pdf.pages)}")
        
        # Check first page
        page = pdf.pages[0]
        tables = page.extract_tables()
        
        if tables:
            print(f"Found {len(tables)} tables on page 1")
            for i, table in enumerate(tables):
                print(f"--- Table {i+1} Sample (First 3 rows) ---")
                df = pd.DataFrame(table)
                print(df.head(3))
        else:
            print("No tables found on page 1")

if __name__ == "__main__":
    inspect_table("20251031-01-r707jyuusoku.pdf")
