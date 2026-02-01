import streamlit as st
import pandas as pd
import time
import traceback
import base64
import json
import os

# --- Config & Assets ---
st.set_page_config(
    page_title="企業主導型一覧更新",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cute SVG Assets (Inline for simplicity)
GEAR_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#888888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3"></circle>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
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
    /* Hide Default Headers/Footers */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* General Font */
    body {
        font-family: 'Helvetica Neue', 'Hiragino Kaku Gothic ProN', sans-serif;
        color: #555;
    }
    
    /* Center Layout Wrapper */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding-top: 3rem;
        text-align: center;
    }
    
    /* Config Button Area */
    .config-area {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999;
    }
    
    /* Upload Box Styling */
    .upload-box {
        border: 2px dashed #dfe6e9;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background-color: #fcfcfc;
        transition: all 0.3s;
        margin: 2rem 0;
    }
    .upload-box:hover {
        border-color: #74b9ff;
        background-color: #f0f8ff;
    }
    
    /* Custom Title */
    .app-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2d3436;
        margin-bottom: 0.5rem;
    }
    .app-subtitle {
        color: #b2bec3;
        margin-bottom: 3rem;
    }
    
    /* Button Styling Override */
    div.stButton > button {
        background-color: #a29bfe !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 0.5rem 2rem !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(162, 155, 254, 0.4) !important;
        transition: all 0.3s !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(162, 155, 254, 0.6) !important;
    }
    
    /* Hide Label of File Uploader */
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
    pass

# --- Session State for Settings Toggle ---
if 'show_settings' not in st.session_state:
    st.session_state['show_settings'] = False

def toggle_settings():
    st.session_state['show_settings'] = not st.session_state['show_settings']

# --- Layout: Settings Button (Top Right) ---
col_head_1, col_head_2 = st.columns([9, 1])
with col_head_2:
    if st.button("⚙️", key="gear_btn", help="設定を開く"):
        toggle_settings()

# --- Settings Modal/Section ---
if st.session_state['show_settings']:
    with st.container():
        st.info("🛠️ 設定エリア")
        with st.expander("認証情報の登録", expanded=True):
            creds_file = st.file_uploader("credentials.json (Google Service Account key)", type=["json"])
        
        default_url = "https://docs.google.com/spreadsheets/d/1VykdvyTvtwpiM-7NeheFQBRfwCV58DTxc8hO1peI1C4/edit"
        sheet_url = st.text_input("Spreadsheet URL", value=default_url)

        
        st.markdown("---")
        st.subheader("🤖 AI設定 (Optional)")
        gemini_key = st.text_input("Gemini API Key", type="password", help="PDFの列をAIで自動判定する場合に入力")
        st.caption("※入力がない場合は従来のルールで読み取ります。")
else:
    creds_file = None

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Title & Cloud Icon
st.markdown(f'{CLOUD_UPLOAD_ICON}', unsafe_allow_html=True)
st.markdown('<div class="app-title">企業主導型一覧更新</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">PDFをアップロードして、リストを自動更新</div>', unsafe_allow_html=True)

# File Uploader (Center)
uploaded_pdf = st.file_uploader("PDF Upload", type=["pdf"])

if uploaded_pdf:
    st.success(f"Filename: {uploaded_pdf.name}")
    
    # Save PDF
    with open("temp_upload.pdf", "wb") as f:
        f.write(uploaded_pdf.getbuffer())

    # Step 1: 更新チェック Button
    if st.button("更新チェックを開始する"):
        
        # Check Creds
        if not os.path.exists("temp_creds.json") and not creds_file:
             st.error("⚙️ 右上の設定ボタンから、認証キー(JSON)をセットしてください。")
             st.session_state['show_settings'] = True
             st.rerun()
        
        if creds_file:
            with open("temp_creds.json", "wb") as f:
                f.write(creds_file.getbuffer())
        
        # Process and store results in session_state
        try:
            with st.spinner("🚀 データ処理を開始します..."):
                # 0. Connect to Google Sheets FIRST (to get headers)
                target_url = sheet_url if 'sheet_url' in locals() else default_url
                handler = SheetsHandler("temp_creds.json", target_url)
                current_df = handler.get_current_data()
                sheet_headers = current_df.columns.tolist()

                # 1. Extract PDF headers and data
                pdf_headers, pdf_data = get_pdf_headers_and_data("temp_upload.pdf")
                
                # 2. AI Header Matching (if key provided)
                header_mapping = {}
                if 'gemini_key' in locals() and gemini_key:
                    ai_result = match_headers_with_gemini(pdf_headers, sheet_headers, gemini_key)
                    
                    if "error" not in ai_result:
                        header_mapping = ai_result
                else:
                    # Fallback: exact name matching
                    for h in pdf_headers:
                        if h in sheet_headers:
                            header_mapping[h] = h
                
                # Store in session state for use by the second button
                st.session_state['pdf_data'] = pdf_data
                st.session_state['header_mapping'] = header_mapping
                st.session_state['sheet_headers'] = sheet_headers
                st.session_state['pdf_headers'] = pdf_headers
                st.session_state['target_url'] = target_url
                st.session_state['ready_to_write'] = True
                
                st.success("✅ 解析完了！下のボタンで書き込みを実行できます。")
                st.rerun()  # Rerun to show the second button
                
        except Exception as e:
            st.error(f"エラー: {e}")
            import traceback
            st.code(traceback.format_exc())

    # Step 2: Show results and write button (only if data is ready)
    if st.session_state.get('ready_to_write', False):
        pdf_data = st.session_state['pdf_data']
        header_mapping = st.session_state['header_mapping']
        sheet_headers = st.session_state['sheet_headers']
        pdf_headers = st.session_state['pdf_headers']
        
        # Show summary
        st.write(f"📋 シート項目: {sheet_headers[:5]}... (全{len(sheet_headers)}個)")
        st.write(f"📋 PDF項目: {pdf_headers[:5]}... (全{len(pdf_headers)}個)")
        st.write(f"✅ {len(pdf_data)} 件のデータを抽出しました。")
        
        matched = sum(1 for v in header_mapping.values() if v is not None)
        st.success(f"AI解析成功! {matched}/{len(pdf_headers)} 項目がマッチしました。")
        
        with st.expander("マッピング詳細"):
            st.json(header_mapping)
        
        with st.expander("プレビュー（最初の5件）"):
            import pandas as pd
            preview_df = pd.DataFrame(pdf_data[:5])
            st.dataframe(preview_df)
        
        st.warning("⚠️ スプレッドシートの既存データを全て消去し、上書きします。")
        
        # The actual write button
        if st.button("🚀 全データを書き換える", type="primary"):
            try:
                with st.spinner("書き込み中..."):
                    target_url = st.session_state['target_url']
                    handler = SheetsHandler("temp_creds.json", target_url)
                    result_msg = handler.clear_and_write_data(pdf_data, header_mapping)
                
                if "Success" in result_msg:
                    st.success(result_msg)
                    st.balloons()
                    # Clear session state after success
                    st.session_state['ready_to_write'] = False
                else:
                    st.error(result_msg)
                    
            except Exception as e:
                st.error(f"書き込みエラー: {e}")
                import traceback
                st.code(traceback.format_exc())

st.markdown('</div>', unsafe_allow_html=True)
