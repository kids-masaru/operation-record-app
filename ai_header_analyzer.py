
import pdfplumber
import json
from google import genai
from google.genai import types

def get_pdf_headers_and_data(pdf_path):
    """
    Extracts the header row(s) and all data rows from the PDF.
    Handles multi-level headers by combining the first two rows.
    Returns: (headers: list[str], data: list[dict])
    """
    all_rows = []
    headers = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Use default extracting settings which usually handle merged cells reasonably well
            tables = page.extract_tables()
            
            for table in tables:
                if not table:
                    continue
                
                # --- Header Extraction Strategy (Page 0, Table 0 only) ---
                start_row_idx = 0
                if page_num == 0 and not headers:
                    # Check if we have enough rows for 2-level header
                    if len(table) >= 2:
                        row0 = [str(cell).strip() if cell else "" for cell in table[0]]
                        row1 = [str(cell).strip() if cell else "" for cell in table[1]]
                        
                        # Forward fill row0 (handle merged cells being None/Empty in pdfplumber)
                        # Example: ['Category', '', ''] -> ['Category', 'Category', 'Category']
                        filled_row0 = []
                        last_val = ""
                        for val in row0:
                            if val:
                                last_val = val
                            filled_row0.append(last_val)
                        
                        # Check if row1 looks like a header (heuristic: not all numbers)
                        # or if we decide to ALWAYS treat first 2 rows as headers for this specific PDF format
                        # Given the user's screenshot, it's definitely a 2-row header format.
                        
                        combined_headers = []
                        for top, bottom in zip(filled_row0, row1):
                            # Case 1: 2-level (Top != Bottom and both exist) -> "Category_Subitem"
                            if top and bottom and top != bottom:
                                combined_headers.append(f"{top}_{bottom}")
                            # Case 2: 1-level spans 2 rows (Top == Bottom) or Bottom is empty -> "Top"
                            elif top:
                                combined_headers.append(top)
                            # Case 3: Top empty, Bottom has text -> "Bottom"
                            elif bottom:
                                combined_headers.append(bottom)
                            else:
                                combined_headers.append(f"Column_{len(combined_headers)}")
                        
                        headers = combined_headers
                        start_row_idx = 2 # Data starts from row 2
                    
                    elif len(table) == 1:
                        # Fallback for single row table
                        headers = [str(cell).strip() if cell else "" for cell in table[0]]
                        start_row_idx = 1

                # --- Data Extraction ---
                # Use the headers we found (or skip if we haven't found headers yet)
                if not headers:
                     continue

                # Iterate rows starting from where data begins
                # For subsequent pages/tables, data usually starts at index 0 
                # UNLESS headers repeat. 
                
                current_loop_start = start_row_idx if (page_num == 0 and table == tables[0]) else 0
                
                for i in range(current_loop_start, len(table)):
                    row = table[i]
                    clean_row = [str(cell).strip() if cell else "" for cell in row]
                    
                    # Skip empty rows
                    if not any(clean_row):
                        continue
                        
                    # Skip if it looks like a repeated header row (fuzzy match)
                    # Use first few columns to check
                    if clean_row[:3] == [h.split('_')[0] for h in headers[:3]]:
                        continue
                    if clean_row[:3] == headers[:3]:
                        continue

                    all_rows.append(clean_row)

    # Convert rows to list of dicts keyed by header
    data = []
    for row in all_rows:
        record = {}
        for i, header in enumerate(headers):
            if i < len(row):
                record[header] = row[i]
            else:
                record[header] = ""
        data.append(record)
    
    return headers, data


def match_headers_with_gemini(pdf_headers, sheet_headers, api_key):
    """
    Uses Gemini to match PDF headers to Spreadsheet headers.
    Returns: dict mapping PDF header -> Spreadsheet header
    """
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are a data mapping assistant.
    
    I have two lists of column headers:
    1. PDF Headers (from a nursery facilities list PDF):
       {json.dumps(pdf_headers, ensure_ascii=False)}
       *Note: Some PDF headers are merged from 2 rows, joined by '_'. 
       Example: "ParentCategory_ChildItem" means the column is "ChildItem" under "ParentCategory".
    
    2. Spreadsheet Headers (the target columns):
       {json.dumps(sheet_headers, ensure_ascii=False)}
    
    Your task: For each PDF header, find the matching Spreadsheet header.
    Headers may have slightly different names but mean the same thing.
    
    Matching Examples:
    - PDF: "施設名称" -> Sheet: "保育施設名"
    - PDF: "保育施設定員_乳児" -> Sheet: "乳児（定員）" (Matches ChildItem and ParentCategory context)
    - PDF: "在籍児童数（従業員枠_自社枠）_1・2歳児" -> Sheet: "1・2歳児（従業員枠_自社枠）"
    
    Return a JSON object where:
    - Keys are the PDF header names (exactly as given)
    - Values are the matching Spreadsheet header names (exactly as given)
    - If no match is found, use null
    
    Only match headers that clearly refer to the same data.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("AI Header Analyzer module ready.")
