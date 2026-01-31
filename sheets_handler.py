
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os

class SheetsHandler:
    def __init__(self, credentials_json, sheet_url):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Determine if credentials_json is a path or content
        if os.path.exists(credentials_json):
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, self.scope)
        else:
            # Assume it's a temp file path or handle dict parsing if needed (simplified for file path now)
            raise FileNotFoundError(f"Credentials file not found: {credentials_json}")
            
        self.client = gspread.authorize(self.creds)
        self.sheet_url = sheet_url
        self.sh = self.client.open_by_url(sheet_url)
        self.worksheet = self.sh.get_worksheet(0) # Assume first sheet

    def get_current_data(self):
        """Fetches all data as a DataFrame."""
        data = self.worksheet.get_all_values()
        headers = data[0]
        rows = data[1:]
        return pd.DataFrame(rows, columns=headers)

    def update_data(self, pdf_df, key_col_sheet="助成決定番号", key_col_pdf="grant_id"):
        """
        Updates the sheet based on matching keys.
        Preserves Column A (index 0).
        """
        # Fetch current data
        current_data = self.worksheet.get_all_values()
        headers = current_data[0]
        
        # Map headers to column indices
        col_map = {name: i for i, name in enumerate(headers)}
        
        if key_col_sheet not in col_map:
            raise ValueError(f"Key column '{key_col_sheet}' not found in Spreadsheet headers.")
            
        key_idx = col_map[key_col_sheet]
        
        # Prepare updates
        # List of Cell objects to batch update
        cells_to_update = []
        
        # Create a lookup for PDF data
        # pdf_df should be standardized. 
        # We need a mapping from Sheet Column Name -> PDF Column Name
        # For now, we'll try to match by name or use a hardcoded map based on common fields
        
        # Simplified mapping for demonstration:
        # Sheet Header : PDF DataFrame Column
        mapping = {
            "施設名": "nursery_name",
            "定員": "capacity",
            "住所": "address",
            "法人名": "corporation_name"
            # Add more as needed
        }
        
        # Iterate through sheet rows (skipping header)
        # We use enumerate starting from 2 (row 1 is header, 1-based index for gspread)
        updated_count = 0
        
        for i, row in enumerate(current_data[1:], start=2):
            sheet_key_val = row[key_idx]
            
            # Find matching row in PDF Data
            match = pdf_df[pdf_df[key_col_pdf].astype(str) == str(sheet_key_val)]
            
            if not match.empty:
                pdf_row = match.iloc[0]
                row_changed = False
                
                for sheet_col, pdf_col in mapping.items():
                    if sheet_col in col_map and pdf_col in pdf_row:
                        col_idx = col_map[sheet_col]
                        new_val = str(pdf_row[pdf_col])
                        current_val = row[col_idx]
                        
                        if new_val != current_val:
                            # Add to update list
                            # gspread Use (row, col) 1-based
                            cells_to_update.append(
                                gspread.Cell(row=i, col=col_idx+1, value=new_val)
                            )
                            row_changed = True
                            
                if row_changed:
                    updated_count += 1
                    
        if cells_to_update:
            print(f"Updating {len(cells_to_update)} cells across {updated_count} rows...")
            self.worksheet.update_cells(cells_to_update)
            return f"Success: Updated {updated_count} rows."
        else:
            return "No changes needed."

    def clear_and_write_data(self, pdf_data, header_mapping):
        """
        Clears all data (except header) and writes the new data.
        
        Args:
            pdf_data: list of dicts, each dict has PDF header names as keys
            header_mapping: dict mapping PDF header -> Spreadsheet header
        """
        print("[DEBUG] clear_and_write_data: START")
        
        # 1. Fetch current headers from spreadsheet
        print("[DEBUG] Step 1: Fetching headers...")
        current_data = self.worksheet.get_all_values()
        if not current_data:
            return "Error: Sheet is empty, cannot find headers."
            
        sheet_headers = current_data[0]
        print(f"[DEBUG] Sheet headers count: {len(sheet_headers)}")
        
        # 2. Build reverse mapping: Spreadsheet header -> column index
        print("[DEBUG] Step 2: Building column index map...")
        sheet_header_to_col = {h: i for i, h in enumerate(sheet_headers)}
        
        # 3. Build the rows to write
        print("[DEBUG] Step 3: Building rows...")
        new_rows = []
        matched_count = 0
        
        for pdf_record in pdf_data:
            row_data = [""] * len(sheet_headers)
            
            for pdf_header, value in pdf_record.items():
                sheet_header = header_mapping.get(pdf_header)
                
                if sheet_header and sheet_header in sheet_header_to_col:
                    col_idx = sheet_header_to_col[sheet_header]
                    row_data[col_idx] = str(value) if value else ""
                    matched_count += 1
            
            if any(row_data):
                new_rows.append(row_data)
        
        print(f"[DEBUG] Built {len(new_rows)} rows, {matched_count} total cell matches")
        
        if not new_rows:
            print("[DEBUG] No rows to write!")
            return "Warning: No data to write (0 rows matched)."
        
        # 4. Clear existing data
        print("[DEBUG] Step 4: Clearing data...")
        try:
            # Use simpler clear method
            self.worksheet.batch_clear(["A2:ZZ10000"])
            print("[DEBUG] Clear successful")
        except Exception as e:
            print(f"[DEBUG] Clear error: {e}")
            return f"Error during clear: {e}"
        
        # 5. Write new data
        print(f"[DEBUG] Step 5: Writing {len(new_rows)} rows...")
        try:
            self.worksheet.update(values=new_rows, range_name="A2")
            print("[DEBUG] Write successful")
            return f"Success: Replaced all data with {len(new_rows)} records."
        except Exception as e:
            print(f"[DEBUG] Write error: {e}")
            return f"Error during write: {e}"

if __name__ == "__main__":
    # Test only if credentials exist
    print("SheetsHandler module ready.")
