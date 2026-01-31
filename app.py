import streamlit as st
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
try:
    from kintone_client import get_nursery_data, get_bed_data
    from data_processor import merge_data
    from excel_manager import update_excel
except ImportError:
    st.error("Modules not found. Please ensure project structure.")

st.set_page_config(page_title="運営実績自動更新アプリ", layout="wide")

st.title("📊 運営実績 自動更新ツール")

# Sidebar: Config
with st.sidebar:
    st.header("設定")
    # Load defaults from env
    default_nursery_token = os.getenv("KINTONE_API_TOKEN_NURSERY", "")
    default_client_token = os.getenv("KINTONE_API_TOKEN_CLIENT", "")
    default_gemini_key = os.getenv("GEMINI_API_KEY", "")

    kintone_token = st.text_input("Kintone API Token (保育園: App 218)", value=default_nursery_token, type="password")
    bed_token = st.text_input("Kintone API Token (クライアント/病床: App 32)", value=default_client_token, type="password")
    gemini_key = st.text_input("Gemini API Key", value=default_gemini_key, type="password")
    
    target_date = st.date_input("更新基準日")

# Main: File Upload
uploaded_file = st.file_uploader("前月の運営実績Excelをアップロード", type=["xlsx"])

if st.button("更新開始", type="primary"):
    if not (uploaded_file and kintone_token and bed_token):
        st.error("必要な情報（Excel, トークン）が不足しています。")
        st.stop()
        
    # 1. Fetch Data
    with st.status("データ取得中...", expanded=True) as status:
        try:
            st.write("Kintoneから保育園情報を取得中...")
            nursery_records = get_nursery_data(kintone_token)
            st.write(f"保育園情報: {len(nursery_records)}件 取得")
            
            st.write("Kintoneから病床数データを取得中...")
            bed_records = get_bed_data(bed_token)
            st.write(f"病床数データ: {len(bed_records)}件 取得")
            
            status.update(label="データ取得完了", state="complete", expanded=False)
        except Exception as e:
            st.error(f"エラー発生: {e}")
            st.stop()

    # 2. Process Data
    with st.status("データ処理＆名寄せ中...", expanded=True) as status:
        try:
            os.environ["GEMINI_API_KEY"] = gemini_key or ""
            merged_data = merge_data(nursery_records, bed_records)
            st.write(f"結合完了: {len(merged_data)}件")
            status.update(label="処理完了", state="complete", expanded=False)
        except Exception as e:
            st.error(f"データ処理エラー: {e}")
            st.stop()

    # 3. Excel Update
    with st.status("Excel更新中...", expanded=True) as status:
        try:
            # Create a copy in memory
            wb = update_excel(uploaded_file, merged_data, target_date)
            
            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            status.update(label="Excel生成完了", state="complete", expanded=False)
            
            # Download Button
            st.success("処理が完了しました！")
            st.download_button(
                label="更新済みExcelをダウンロード",
                data=output,
                file_name=f"運営実績_{target_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Excel更新エラー: {e}")
            st.stop()
