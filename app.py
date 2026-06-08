import streamlit as st
from supabase import create_client, Client

# ページの設定
st.set_page_config(page_title="予備試験 論証暗記ツール Pro", layout="wide")

# ==========================================
# 🔴 ご自身のSupabaseのURLとAPIキー（anon key）に書き換えてください
# ==========================================
SUPABASE_URL = "https://ymozpxiqdsuhhhnizfey.supabase.co"
SUPABASE_KEY = "sb_publishable_IaB15FYlOKVmLwS_RskAgA_WacwtLeV"

# Supabaseクライアントの初期化（キャッシュして高速化）
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- セッション状態（データ保持）の初期化 ---
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_answered" not in st.session_state:
    st.session_state.is_answered = False

# ==========================================
# 🔓 画面1：ログイン画面
# ==========================================
if not st.session_state.user_id:
    st.title("⚖️ SHIBA Legal 暗記アプリ (Web版)")
    st.write("一般公開用・マルチユーザー対応システム")
    
    with st.form("login_form"):
        user_input = st.text_input("あなたのユーザーID（名前など半角英数字）を入力してください", placeholder="例: takuya, sakura")
        submit_login = st.form_submit_button("ログインして始める")
        
        if submit_login:
            if user_input.strip():
                st.session_state.user_id = user_input.strip()
                st.rerun()
            else:
                st.error("ユーザーIDを入力してください。")
    st.stop()

# ==========================================
# 📚 画面2：メインの暗記・管理画面（ログイン後）
# ==========================================

# データの取得関数
def fetch_data():
    res = supabase.table("arguments").select("*").eq("user_id", st.session_state.user_id).order("id").execute()
    return res.data

data_list = fetch_data()

# サイドバー：論証一覧
st.sidebar.title(f"📋 {st.session_state.user_id} の論証")
if st.sidebar.button("🔄 データを同期・更新"):
    st.rerun()

selected_issue = None
if data_list:
    options = [f"{item['issue']} [{item['status']}]" for item in data_list]
    # 前回の選択位置を維持（配列の範囲内なら）
    default_idx = st.session_state.current_index if st.session_state.current_index < len(data_list) else 0
    selected_option = st.sidebar.radio("論点を選択:", options, index=default_idx)
    
    # 選択されたインデックスを取得
    current_idx = options.index(selected_option)
    if current_idx != st.session_state.current_index:
        st.session_state.current_index = current_idx
        st.session_state.is_answered = False
        st.rerun()
        
    current_arg = data_list[st.session_state.current_index]
else:
    current_arg = None

# メイン領域のタブ
tab_study, tab_manage = st.tabs(["✍️ 暗記テスト", "🚀 新しい論証を追加"])

# --- タブ1：暗記テスト ---
with tab_study:
    if current_arg:
        st.subheader(f"問題: {current_arg['issue']}")
        
        # 本試験を意識したタイピングエリア
        user_typed = st.text_area(
            "あなたの解答入力欄（本試験のつもりでタイピングしてください）", 
            height=200, 
            placeholder="ここに論証を入力...", 
            key=f"input_{current_arg['id']}",
            disabled=st.session_state.is_answered
        )
        
        # --- 👉 【重要】ブラウザでのチラ見機能の実装 ---
        # HTML/CSSを使って「ボタンを押している間だけ文字を浮き上がらせる」特殊なボタンを配置します
        st.write("👇 **下のボタンをマウスで「左クリックしたまま長押し」している間だけ、解答がチラ見できます**")
        
        st.markdown(
            f"""
            <style>
            .peek-button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #34495e;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                cursor: pointer;
                user-select: none;
                margin-bottom: 10px;
            }}
            .peek-button:active + .answer-box {{
                display: block !important;
            }}
            .answer-box {{
                display: none;
                padding: 15px;
                background-color: #1e272e;
                border-left: 5px solid #2ecc71;
                border-radius: 4px;
                font-family: monospace;
                white-space: pre-wrap;
                color: #2ecc71;
                margin-top: 10px;
            }}
            </style>
            
            <div class="peek-button">👀 ここを左クリック長押しで解答をチラ見</div>
            <div class="answer-box">{current_arg['content']}</div>
            """, 
            unsafe_allow_html=True
        )
        
        st.write("---")
        
        # 答え合わせとステータス更新
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("解答を確定して答え合わせ", type="primary"):
                st.session_state.is_answered = True
                st.rerun()
                
        if st.session_state.is_answered:
            st.success("【模範解答】")
            st.code(current_arg['content'], language="text")
            
            with col2:
                st.write("自己評価を選択して次へ:")
                c_p, c_r, c_b = st.columns(3)
                
                def update_status(status):
                    supabase.table("arguments").update({"status": status}).eq("id", current_arg["id"]).execute()
                    st.session_state.is_answered = False
                    # 次の問題へ
                    st.session_state.current_index = (st.session_state.current_index + 1) % len(data_list)
                    st.toast(f"ステータスを【{status}】に更新しました！")
                    st.rerun()
                    
                if c_p.button("完璧🟢"): update_status("完璧")
                if c_r.button("要補強🟡"): update_status("要補強")
                if c_b.button("不可🔴"): update_status("不可")
    else:
        st.info("右側のサイドバー、または「新しい論証を追加」タブから、まずは論証を登録してください。")

# --- タブ2：論証の追加・管理 ---
with tab_manage:
    st.subheader("新しい論証データをクラウドに登録")
    new_issue = st.text_input("新規論点名 (例: 生存権の法的性格（憲法25条）)")
    new_content = st.text_area("論証本文 (模範解答)", height=300)
    
    if st.button("🚀 データベースに保存"):
        if new_issue.strip() and new_content.strip():
            supabase.table("arguments").insert({
                "user_id": st.session_state.user_id,
                "issue": new_issue.strip(),
                "content": new_content.strip(),
                "status": "未着手"
            }).execute()
            st.success(f"『{new_issue}』を登録しました！「暗記テスト」タブやサイドバーを確認してください。")
            st.rerun()
        else:
            st.error("論点名と本文の両方を入力してください。")