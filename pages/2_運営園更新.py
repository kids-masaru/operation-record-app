import streamlit as st
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="運営園更新",
    page_icon="📊",
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

st.title("📊 運営園更新ツール")
st.caption("Kintoneからデータを取得し、運営実績Excelを自動更新します")

st.markdown("---")

# Sidebar: Navigation & Status
with st.sidebar:
    st.header("📋 メニュー")
    st.page_link("app.py", label="🏠 ホーム")
    st.page_link("pages/1_企業主導型一覧更新.py", label="📄 企業主導型一覧更新")
    st.page_link("pages/2_運営園更新.py", label="📊 運営園更新")
    st.markdown("---")
    st.subheader("⚙️ 環境変数ステータス")
    st.write(f"Kintone (保育園): {'✅' if KINTONE_TOKEN_NURSERY else '❌'}")
    st.write(f"Kintone (クライアント): {'✅' if KINTONE_TOKEN_CLIENT else '❌'}")
    st.write(f"Gemini API: {'✅' if GEMINI_API_KEY else '❌'}")
    if not KINTONE_TOKEN_NURSERY or not KINTONE_TOKEN_CLIENT:
        st.caption("💡 Railway Variables で設定してください")
    st.markdown("---")
    target_date = st.date_input("📅 更新基準日")

# Check if required env vars are set
if not KINTONE_TOKEN_NURSERY or not KINTONE_TOKEN_CLIENT:
    st.error("⚠️ Kintone APIトークンが設定されていません。Railway Variables で以下を設定してください：")
    st.code("KINTONE_API_TOKEN_NURSERY\nKINTONE_API_TOKEN_CLIENT")
    st.stop()

# Main: File Upload
uploaded_file = st.file_uploader("前月の運営実績Excelをアップロード", type=["xlsx"])

if st.button("更新開始", type="primary"):
    if not uploaded_file:
        st.error("Excelファイルをアップロードしてください")
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
            wb = update_excel(uploaded_file, merged_data, target_date)
            
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            status.update(label="Excel生成完了", state="complete", expanded=False)
            
            st.success("処理が完了しました！")
            st.download_button(
                label="📥 更新済みExcelをダウンロード",
                data=output,
                file_name=f"運営実績_{target_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Excel更新エラー: {e}")
            st.stop()
