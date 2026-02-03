import streamlit as st
import pandas as pd
import traceback
import json
import os

# --- Config & Assets ---
st.set_page_config(
    page_title="企業主導型一覧更新",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

CLOUD_UPLOAD_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="#74b9ff" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path>
  <polyline points="16 16 12 12 8 16"></polyline>
  <line x1="12" y1="12" x2="12" y2="21"></line>
</svg>
"""

CLOUD_UPLOAD_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="#74b9ff" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path>
  <polyline points="16 16 12 12 8 16"></polyline>
  <line x1="12" y1="12" x2="12" y2="21"></line>
</svg>
"""

# Custom CSS
st.markdown("""
<style>
    footer {visibility: hidden;}
    body {
        font-family: 'Helvetica Neue', 'Hiragino Kaku Gothic ProN', sans-serif;
        color: #555;
    }
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
        background-color: #a29bfe !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 0.5rem 2rem !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(162, 155, 254, 0.4) !important;
    }
    div[data-testid="stFileUploader"] label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Import logic
try:
    from sheets_handler import SheetsHandler
    from ai_header_analyzer import get_pdf_headers_and_data, match_headers_with_gemini
except ImportError:
    st.error("必要なモジュールが見つかりません")

# --- Load Environment Variables ---
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL", "https://docs.google.com/spreadsheets/d/1VykdvyTvtwpiM-7NeheFQBRfwCV58DTxc8hO1peI1C4/edit")

# Write credentials to temp file if env var is set
if GOOGLE_CREDS_JSON:
    try:
        creds_data = json.loads(GOOGLE_CREDS_JSON)
        with open("temp_creds.json", "w") as f:
            json.dump(creds_data, f)
    except json.JSONDecodeError:
        st.error("GOOGLE_CREDENTIALS_JSON の形式が正しくありません")

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Title & Cloud Icon
st.markdown(f'{CLOUD_UPLOAD_ICON}', unsafe_allow_html=True)
st.markdown('<div class="app-title">企業主導型一覧更新</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">PDFをアップロードして、リストを自動更新</div>', unsafe_allow_html=True)


# Show env status in sidebar
# Sidebar: Navigation
with st.sidebar:
    st.header("📋 メニュー")
    st.page_link("pages/1_企業主導型一覧更新.py", label="企業主導型一覧更新")
    st.page_link("pages/2_運営園更新.py", label="運営園更新")
    st.markdown("---")

# File Uploader (Center)
uploaded_pdf = st.file_uploader("PDF Upload", type=["pdf"])

if uploaded_pdf:
    st.success(f"✅ {uploaded_pdf.name}")
    
    # Save PDF
    with open("temp_upload.pdf", "wb") as f:
        f.write(uploaded_pdf.getbuffer())

    # Step 1: 更新チェック & 自動書き換え Button
    if st.button("更新チェックを開始する（自動書き換え）", type="primary"):
        
        # Check Creds
        if not os.path.exists("temp_creds.json"):
            st.error("⚠️ 環境変数 GOOGLE_CREDENTIALS_JSON が設定されていません。Railway Variables で設定してください。")
            st.stop()
        
        # Process and store results
        try:
            with st.status("🚀 データ処理を実行中...", expanded=True) as status:
                st.write("Google Sheetsに接続中...")
                # 0. Connect to Google Sheets FIRST (to get headers)
                handler = SheetsHandler("temp_creds.json", SPREADSHEET_URL)
                current_df = handler.get_current_data()
                sheet_headers = current_df.columns.tolist()

                st.write("PDFからデータを抽出中...")
                # 1. Extract PDF headers and data
                pdf_headers, pdf_data = get_pdf_headers_and_data("temp_upload.pdf")
                st.write(f"抽出完了: {len(pdf_data)}件のデータ")
                
                # 2. AI Header Matching (if key provided)
                header_mapping = {}
                if GEMINI_API_KEY:
                    st.write("AIによるヘッダー解析中...")
                    ai_result = match_headers_with_gemini(pdf_headers, sheet_headers, GEMINI_API_KEY)
                    if "error" not in ai_result:
                        header_mapping = ai_result
                else:
                    st.write("項目名マッチング中...")
                    # Fallback: exact name matching
                    for h in pdf_headers:
                        if h in sheet_headers:
                            header_mapping[h] = h
                
                matched = sum(1 for v in header_mapping.values() if v is not None)
                st.write(f"マッピング完了: {matched}/{len(pdf_headers)} 項目マッチ")
                
                # 3. Write Data Immediately
                st.write("Google Sheetsへの書き込みを開始...")
                result_msg = handler.clear_and_write_data(pdf_data, header_mapping)
                
                if "Success" in result_msg:
                    status.update(label="✅ 全工程完了！", state="complete", expanded=False)
                    st.success(result_msg)
                    st.balloons()
            
                    with st.expander("詳細レポート"):
                        st.json(header_mapping)
                        st.dataframe(pd.DataFrame(pdf_data[:5]))
                else:
                    status.update(label="❌ エラー発生", state="error")
                    st.error(result_msg)
                
        except Exception as e:
            st.error(f"エラー: {e}")
            st.code(traceback.format_exc())

st.markdown('</div>', unsafe_allow_html=True)
