import streamlit as st
from supabase import create_client, Client

# ページの設定
st.set_page_config(page_title="予備試験 論証暗記ツール Pro", layout="wide")

# ==========================================
# 🔴 ご自身のSupabaseのURLとAPIキー（anon key）に書き換えてください
# ==========================================
SUPABASE_URL = "https://ymozpxiqdsuhhnizfey.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inltb3pweGlxZHN1aGhobml6ZmV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5Mjk1MDgsImV4cCI6MjA5NjUwNTUwOH0.ooR2slaqn1VbAYZnTQS6wTzOia5ChYUUNDfHsd75gsA"

# Supabaseクライアントの初期化
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
    st.title("SHIVA Legal 論証暗記アプリ")
    st.write("論証のアウトプット・暗記度管理を徹底")
    
    with st.form("login_form"):
        user_input = st.text_input("あなたのユーザーID（名前など半角英数字）を入力してください", placeholder="例: kenta, iseki")
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

# --- サイドバー：論証一覧 & 削除機能 ---
st.sidebar.title(f"{st.session_state.user_id} の論証")
if st.sidebar.button("データを同期・更新"):
    st.rerun()

current_arg = None
if data_list:
    options = [f"{item['issue']} [{item['status']}]" for item in data_list]
    
    # 範囲外エラーを防ぐ安全弁
    if st.session_state.current_index >= len(data_list):
        st.session_state.current_index = 0
        
    selected_option = st.sidebar.radio("論点を選択:", options, index=st.session_state.current_index)
    
    # 選択されたインデックスの更新
    current_idx = options.index(selected_option)
    if current_idx != st.session_state.current_index:
        st.session_state.current_index = current_idx
        st.session_state.is_answered = False
        st.rerun()
        
    current_arg = data_list[st.session_state.current_index]
    
    # 🛠️ 削除ボタンの設置
    st.sidebar.write("---")
    with st.sidebar.expander("⚠️ 危険領域（データの削除）"):
        st.write("現在選択中の論証をデータベースから完全に消去します。")
        if st.button("❌ 選択中の論証を削除する", type="primary"):
            # SupabaseからID指定で削除を実行
            supabase.table("arguments").delete().eq("id", current_arg["id"]).execute()
            st.toast(f"『{current_arg['issue']}』を削除しました")
            st.session_state.current_index = max(0, st.session_state.current_index - 1)
            st.session_state.is_answered = False
            st.rerun()
else:
    st.sidebar.info("論証が登録されていません。")

# メイン領域のタブ
tab_study, tab_manage = st.tabs(["暗記テスト", "論証の追加・編集"])

# --- タブ1：暗記テスト ---
with tab_study:
    if current_arg:
        st.subheader(f"問題: {current_arg['issue']}")
        
        user_typed = st.text_area(
            "解答入力欄", 
            height=200, 
            placeholder="ここに論証を入力...", 
            key=f"input_{current_arg['id']}",
            disabled=st.session_state.is_answered
        )
        
        # 💡 【対策】インデントをwithブロック内に正しく修正
        safe_content = current_arg['content'].replace("\n", "<br>")
        
        st.write("↓ **下のボタン長押しで解答を一時表示**")
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
            
            <div class="peek-button">解答を一時表示</div>
            <div class="answer-box">{safe_content}</div>
            """, 
            unsafe_allow_html=True
        )
        
        st.write("---")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("解答確認", type="primary"):
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
                    if len(data_list) > 1:
                        st.session_state.current_index = (st.session_state.current_index + 1) % len(data_list)
                    st.toast(f"ステータスを【{status}】に更新しました！")
                    st.rerun()
                    
                if c_p.button("完璧🟢"): update_status("完璧")
                if c_r.button("要補強🟡"): update_status("要補強")
                if c_b.button("不可🔴"): update_status("不可")
    else:
        st.info("右側のサイドバー、または「論証の追加・編集」タブから、まずは論証を登録してください。")

# --- タブ2：論証の追加・編集 ---
with tab_manage:
    st.subheader("論証データの登録・編集変更")
    
    # ラジオボタンで「新規追加モード」か「編集モード」かを選べるようにする
    manage_mode = st.radio("操作を選択してください:", ["＋ 新しい論証を追加する", "現在サイドバーで選択中の論証を修正する"], horizontal=True)
    
    if manage_mode == "＋ 新しい論証を追加する":
        edit_issue = ""
        edit_content = ""
        btn_text = "新規データをデータベースに保存"
    else:
        if current_arg:
            edit_issue = current_arg["issue"]
            edit_content = current_arg["content"]
            btn_text = "修正内容を上書き保存する"
        else:
            st.warning("編集するデータがありません。")
            st.stop()
            
    # 入力フォーム（モードに応じて初期値が自動で変わります）
    input_issue = st.text_input("論点名", value=edit_issue)
    input_content = st.text_area("論証本文 (模範解答)", value=edit_content, height=300)
    
    if st.button(btn_text):
        if input_issue.strip() and input_content.strip():
            if manage_mode == "＋ 新しい論証を追加する":
                # 新規追加の処理
                supabase.table("arguments").insert({
                    "user_id": st.session_state.user_id,
                    "issue": input_issue.strip(),
                    "content": input_content.strip(),
                    "status": "未着手"
                }).execute()
                st.success(f"『{input_issue}』を新しく登録しました！")
            else:
                # 🛠️ 編集（上書き更新）の処理
                supabase.table("arguments").update({
                    "issue": input_issue.strip(),
                    "content": input_content.strip()
                }).eq("id", current_arg["id"]).execute()
                st.success(f"『{input_issue}』の修正を上書き保存しました！")
                
            st.rerun()
        else:
            st.error("論点名と本文の両方を入力してください。")
