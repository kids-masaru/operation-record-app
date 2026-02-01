import streamlit as st

st.set_page_config(
    page_title="保育園管理ツール",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful top page
st.markdown("""
<style>
    /* Keep header visible for sidebar toggle */
    footer {visibility: hidden;}
    
    /* Card styling */
    .menu-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        color: white;
        text-align: center;
        margin: 1rem 0;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    .menu-card-blue {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    }
    .menu-card-green {
        background: linear-gradient(135deg, #55efc4 0%, #00b894 100%);
    }
    
    .card-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .card-desc {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Center title */
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        color: #2d3436;
        margin-bottom: 0.5rem;
    }
    .main-subtitle {
        text-align: center;
        color: #636e72;
        margin-bottom: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Main Title
st.markdown('<div class="main-title">🏠 保育園管理ツール</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">左のサイドバーから機能を選んでください</div>', unsafe_allow_html=True)

st.markdown("---")

# Feature Cards (Display for visual guidance)
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="menu-card menu-card-blue">
        <div class="card-icon">📄</div>
        <div class="card-title">企業主導型一覧更新</div>
        <div class="card-desc">PDFから保育施設情報を抽出し、<br>Google Sheetsを自動更新します</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("📍 サイドバー → 「企業主導型一覧更新」")

with col2:
    st.markdown("""
    <div class="menu-card menu-card-green">
        <div class="card-icon">📊</div>
        <div class="card-title">運営園更新</div>
        <div class="card-desc">Kintoneからデータを取得し、<br>運営実績Excelを自動更新します</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("📍 サイドバー → 「運営園更新」")

st.markdown("---")

# Instructions
with st.expander("📖 使い方", expanded=False):
    st.markdown("""
    ### 企業主導型一覧更新
    1. サイドバーから「企業主導型一覧更新」を選択
    2. 設定ボタン（⚙️）でGoogle認証情報とAPIキーを設定
    3. PDFをアップロードして更新を実行
    
    ### 運営園更新
    1. サイドバーから「運営園更新」を選択
    2. KintoneのAPIトークンを入力
    3. Excelをアップロードして更新を実行
    """)
