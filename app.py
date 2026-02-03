import streamlit as st

st.set_page_config(
    page_title="保育園管理ツール",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Redirect to the first page immediately
st.switch_page("pages/1_企業主導型一覧更新.py")
