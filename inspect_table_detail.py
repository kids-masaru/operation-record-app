
import pdfplumber
import json

def inspect_table_detail(file_path):
    with pdfplumber.open(file_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        
        if tables:
            first_table = tables[0]
            print(f"Row count: {len(first_table)}")
            for i, row in enumerate(first_table[:5]):
                # Replace None with "None" string for printing
                clean_row = [str(x).replace('\n', ' ') if x else "None" for x in row]
                print(f"Row {i}: {json.dumps(clean_row, ensure_ascii=False)}")
        else:
            print("No tables found")

if __name__ == "__main__":
    inspect_table_detail("20251031-01-r707jyuusoku.pdf")
