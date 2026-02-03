import streamlit as st
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sidebar: Navigation
with st.sidebar:
    st.header("📋 メニュー")
    st.page_link("pages/1_企業主導型一覧更新.py", label="企業主導型一覧更新")
    st.page_link("pages/2_運営園更新.py", label="運営園更新")
    st.markdown("---")

st.set_page_config(
    page_title="運営園更新",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modules
try:
    from kintone_client import get_nursery_data, get_bed_data
    from data_processor import merge_data
    from excel_manager import update_excel
except ImportError:
    st.error("必要なモジュールが見つかりません")

# --- Load Environment Variables ---
KINTONE_TOKEN_NURSERY = os.getenv("KINTONE_API_TOKEN_NURSERY", "")
KINTONE_TOKEN_CLIENT = os.getenv("KINTONE_API_TOKEN_CLIENT", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
import json
# Write credentials to temp file if env var is set
if GOOGLE_CREDS_JSON:
    try:
        creds_data = json.loads(GOOGLE_CREDS_JSON)
        with open("temp_creds.json", "w") as f:
            json.dump(creds_data, f)
    except json.JSONDecodeError:
        st.error("GOOGLE_CREDENTIALS_JSON の形式が正しくありません")

# Custom CSS
st.markdown("""
<style>
    footer {visibility: hidden;}
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding-top: 2rem;
        text-align: center;
    }
    .app-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2d3436;
        margin-bottom: 0.5rem;
    }
    .app-subtitle {
        color: #b2bec3;
        margin-bottom: 2rem;
    }
    div.stButton > button {
        background-color: #00cec9 !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 0.5rem 2rem !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0, 206, 201, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

SYNC_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="#00cec9" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/>
</svg>
"""

st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.markdown(f'{SYNC_ICON}', unsafe_allow_html=True)
st.markdown('<div class="app-title">運営園更新リスト作成</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Kintoneから最新データを取得し、Excelを作成</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

import datetime

# Main: Update Button
target_date = datetime.date.today()

if st.button("更新データを作成する", type="primary"):
    template_path = "sample.xlsm"
    
    if not os.path.exists(template_path):
        # Fallback to xlsx if xlsm not found (for smooth transition)
        if os.path.exists("sample.xlsx"):
            template_path = "sample.xlsx"
            st.warning("⚠️ sample.xlsmが見つからないため、sample.xlsxを使用します。")
        else:
            st.error(f"⚠️ テンプレートファイルが見つかりません: {template_path}")
            st.stop()
        
    # 1. Fetch Data
    with st.status("データ取得中...", expanded=True) as status:
        try:
            st.write("Kintoneから保育園情報を取得中...")
            nursery_records = get_nursery_data(KINTONE_TOKEN_NURSERY)
            st.write(f"保育園情報: {len(nursery_records)}件 取得")
            
            st.write("Kintoneから病床数データを取得中...")
            bed_records = get_bed_data(KINTONE_TOKEN_CLIENT)
            st.write(f"病床数データ: {len(bed_records)}件 取得")
            
            status.update(label="データ取得完了", state="complete", expanded=False)
        except Exception as e:
            st.error(f"エラー発生: {e}")
            st.stop()

    # 2. Process Data
    with st.status("データ処理＆名寄せ中...", expanded=True) as status:
        try:
            os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY or ""
            merged_data = merge_data(nursery_records, bed_records)
            st.write(f"結合完了: {len(merged_data)}件")
            status.update(label="処理完了", state="complete", expanded=False)
        except Exception as e:
            st.error(f"データ処理エラー: {e}")
            st.stop()

    # 3. Excel Update
    with st.status("Excel更新中...", expanded=True) as status:
        try:
            # Pass the local filename directly
            wb = update_excel(template_path, merged_data, target_date)
            
            # Write Today's Date to N1
            ws = wb.worksheets[0]
            ws['N1'] = target_date.strftime("%Y/%m/%d")
            
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            status.update(label="Excel生成完了", state="complete", expanded=False)
            
        except Exception as e:
            st.error(f"Excel更新エラー: {e}")
            st.stop()
            
    # 4. Google Sheets Sync
    target_sheet_url = "https://docs.google.com/spreadsheets/d/14ftSq0cV8EEUJ08LDJwqQvZrCOJqZeJwLIStXyzSkaI/edit?gid=1627985378#gid=1627985378"
    target_sheet_name = "貼り付け用‗運営園"
    
    with st.status("Google Sheetsに同期中...", expanded=True) as status:
        try:
            # Extract data from the first worksheet of the GENERATED workbook
            ws = wb.worksheets[0]
            # Convert worksheet to list of lists (values only)
            data_to_sync = []
            for row in ws.iter_rows(values_only=True):
                # Convert datetime objects to string if needed, or rely on gspread's handling
                # Gspread usually handles basic types. Dates might need formatting.
                # Let's simple-cast everything to str to be safe, or let gspread handle it.
                # Actually, gspread handles strings best.
                row_data = []
                for cell in row:
                    if isinstance(cell, (datetime.date, datetime.datetime)):
                        row_data.append(cell.strftime("%Y/%m/%d"))
                    elif cell is None:
                        row_data.append("")
                    else:
                        row_data.append(str(cell))
                data_to_sync.append(row_data)

            # Check creds again (should exist if we reached here, but safe check)
            creds_file = "temp_creds.json"
            if not os.path.exists(creds_file):
                # Try to generate it from env if missing (though Page 1 or App start should have set it)
                 if GOOGLE_CREDS_JSON:
                     try:
                         with open(creds_file, "w") as f:
                             json.dump(json.loads(GOOGLE_CREDS_JSON), f)
                     except: pass
            
            if os.path.exists(creds_file):
                from sheets_handler import SheetsHandler
                handler = SheetsHandler(creds_file, target_sheet_url, target_sheet_name)
                
                # Debug Info
                row_count = len(data_to_sync)
                # st.write(f"同期対象データ: {row_count} 行") # Inside status
                
                if row_count == 0:
                    status.update(label="⚠️ データが空です", state="error", expanded=True)
                    sync_status_msg = "⚠️ 同期対象のデータがありませんでした"
                    sync_success = False
                else:
                    sync_result = handler.write_values(data_to_sync)
                    
                    if "Success" in sync_result:
                        status.update(label="✅ Google Sheets同期完了", state="complete", expanded=False)
                        sync_status_msg = f"✅ スプレッドシート ({row_count}行) への反映に成功しました"
                        sync_success = True
                    else:
                        status.update(label="⚠️ 同期エラー", state="error", expanded=True)
                        sync_status_msg = f"❌ 同期失敗: {sync_result}"
                        sync_success = False
            else:
                status.update(label="⚠️ 認証エラー", state="error", expanded=True)
                sync_status_msg = "⚠️ Google認証情報がないため、同期できませんでした"
                sync_success = False
                
        except Exception as e:
            status.update(label="❌ エラー発生", state="error", expanded=True)
            sync_status_msg = f"❌ 同期処理中にエラーが発生しました: {e}"
            sync_success = False

    # Show result explicitly outside the collapsed status
    if sync_success:
        st.success(sync_status_msg)
    else:
        st.error(sync_status_msg)

    st.success("処理が完了しました！")
    
    # Determine extension based on template (preserve xlsm if source is xlsm)
    is_xlsm = template_path.lower().endswith(".xlsm")
    ext = "xlsm" if is_xlsm else "xlsx"
    mime_type = "application/vnd.ms-excel.sheet.macroEnabled.12" if is_xlsm else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    st.download_button(
        label="📥 更新済みExcelをダウンロード",
        data=output,
        file_name=f"運営実績_{target_date.strftime('%Y%m%d')}.{ext}",
        mime=mime_type
    )
