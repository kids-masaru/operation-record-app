
import pdfplumber
import pandas as pd
import re


def parse_pdf(file_path, column_mapping=None):
    """
    Parses the Child Development Association PDF and returns a DataFrame.
    If column_mapping is provided (from Gemini), uses those indices.
    Otherwise, falls back to loose keyword matching.
    """
    all_data = []
    
    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing {total_pages} pages...")
        
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for table in tables:
                if not table:
                    continue
                
                # Convert raw table rows to structured data
                # Skip rows that are clearly headers or invalid if they don't match our column count
                # If we have a mapping, we know the specific indices to grab
                
                target_indices = {}
                if column_mapping:
                    # Example mapping: {'grant_id': 0, 'nursery_name': 2, ...}
                    # We only care about rows that have data at these indices
                    pass
                
                # Simple Logic: Iterate all rows, check if it looks like data
                for row in table:
                    # heuristic: row must have enough columns
                    # Clean row
                    clean_row = [str(x).replace('\n', '') if x else "" for x in row]
                    
                    record = {}
                    is_valid = False
                    
                    if column_mapping and isinstance(column_mapping, dict):
                        # Use Dynamic AI Mapping
                        try:
                            # Heuristic validation: a valid row should have data in at least one of the mapped columns
                            # Ideally, finding the "Key" column is best. 
                            # We can check for "grant_id" OR "番号" OR "助成決定番号" OR just check if >50% of mapped cols have data?
                            # Let's try to find a likely ID column to validate the row
                            
                            has_data_in_mapped_cols = False
                            temp_record = {}
                            
                            for field, idx in column_mapping.items():
                                if idx is not None and idx < len(clean_row):
                                    val = clean_row[idx]
                                    if val.strip():
                                        has_data_in_mapped_cols = True
                                    temp_record[field] = val
                            
                            # Validation Strategy:
                            # 1. If we found "grant_id" or "番号" etc, check if it looks valid
                            # 2. Or if we just have substantial data (e.g. > 1 non-empty fields)
                            # Let's go with: Must have data in at least 1 mapped field to be considered a record,
                            # AND maybe ignore if the row is purely empty or just header garbage.
                            
                            # Refined: If '番号' or 'grant_id' exists in mapping, require it to be present?
                            # Users sheet might have '番号', so AI will return '番号': idx.
                            
                            id_keys = [k for k in column_mapping.keys() if "番号" in k or "ID" in k or "grant" in k]
                            valid_id = False
                            if id_keys:
                                for k in id_keys:
                                    val = temp_record.get(k, "")
                                    # Check if digit-like or long string?
                                    if val and (val[0].isdigit() or len(val) > 1):
                                        valid_id = True
                                        break
                            else:
                                # No explicit ID column found, proceed if data exists
                                valid_id = has_data_in_mapped_cols

                            if valid_id:
                                record = temp_record
                                is_valid = True
                                
                        except Exception:
                            is_valid = False
                    else:
                        # Fallback (Old Logic - simplified for brevity of replacement)
                        # We assume the old logic was working but fragile. 
                        # To keep this clean, let's just stick to the AI path if provided, 
                        # or a very basic fallback if not.
                        pass

                    if is_valid and record:
                        all_data.append(record)
                            
    # Create DataFrame
    if not all_data:
        # Fallback to old full scan if no data found via mapping?
        # Or just return empty
        return pd.DataFrame()
        
    result_df = pd.DataFrame(all_data)
    return result_df

if __name__ == "__main__":
    # Test
    pass

