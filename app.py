import streamlit as st
from github import Github
import json
import base64
import time
import textwrap

# ==========================================
# 1. 基礎設定
# ==========================================
st.set_page_config(
    page_title="寶可夢科技圖鑑 V14.0",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

if 'selected_index' not in st.session_state:
    st.session_state.selected_index = 0 

# ==========================================
# 2. CSS 樣式 (關鍵修改)
# ==========================================
st.markdown("""
    <style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    :root {
        --ui-cyan: #30a7d7;
        --screen-bg: #1a1a1a;
        --active-color: #ffd700;
    }

    .stApp { background-color: #333 !important; color: white !important; }
    header, footer {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }

    /* --- 上方螢幕 --- */
    .display-box {
        background: radial-gradient(circle at center, #2a2a2a 0%, #000 100%);
        border: 2px solid #555; border-bottom: 4px solid var(--ui-cyan);
        border-radius: 10px; position: relative;
        height: 320px; width: 100%; overflow: hidden;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8); margin-bottom: 10px;
    }
    .tech-info { text-align: center; position: relative; z-index: 20; }
    .tech-id { font-family: monospace; color: var(--ui-cyan); font-weight: bold; font-size: 1.1rem; letter-spacing: 2px;}
    .tech-name { font-size: 1.8rem; font-weight: bold; color: #fff; text-shadow: 0 0 10px var(--ui-cyan); margin-top: -5px;}

    .glow-ring {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(48, 167, 215, 0.5) 0%, transparent 70%);
        border-radius: 50%; z-index: 1; pointer-events: none;
    }
    .pokemon-img-main {
        position: relative; z-index: 10; height: 200px; width: auto; object-fit: contain;
        filter: drop-shadow(0 0 15px rgba(48, 167, 215, 0.6));
        animation: float 4s ease-in-out infinite;
    }

    /* --- [關鍵修改] 下方列表：透明按鈕覆蓋術 --- */
    
    /* 1. 圖片容器 */
    .icon-container {
        display: flex; justify-content: center; align-items: center;
        width: 100%; height: 60px; /* 固定高度 */
        position: relative; z-index: 1; /* 在按鈕下層 */
    }
    
    /* 2. 小圓圖樣式 */
    .list-img {
        width: 55px; height: 55px; object-fit: contain;
        background: #000; border-radius: 50%; 
        border: 2px solid #444; padding: 2px;
        transition: transform 0.2s;
    }
    
    /* 選中時的高亮 */
    .active-border {
        border-color: var(--active-color) !important;
        box-shadow: 0 0 10px var(--active-color);
        transform: scale(1.1);
    }

    /* 3. 將按鈕變透明並覆蓋在圖片上 */
    /* 使用 :has() 選取器：只針對含有 .list-img 的欄位修改按鈕樣式 */
    [data-testid="column"]:has(.list-img) {
        position: relative !important; /* 讓絕對定位參照此欄位 */
    }

    [data-testid="column"]:has(.list-img) button {
        position: absolute !important;
        top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        opacity: 0 !important; /* 隱藏按鈕本體 */
        z-index: 10 !important; /* 蓋在圖片上面 */
        cursor: pointer !important;
        margin: 0 !important; padding: 0 !important;
    }
    
    /* --- [關鍵修改] 手機版強制網格排列 --- */
    @media (max-width: 576px) {
        /* 強制含有圖片的水平區塊不換行 */
        [data-testid="stHorizontalBlock"]:has(.list-img) {
            display: grid !important;
            grid-template-columns: repeat(4, 1fr) !important; /* 強制一行四個 */
            gap: 5px !important;
        }
        
        /* 重設欄位寬度 */
        [data-testid="stHorizontalBlock"]:has(.list-img) [data-testid="column"] {
            width: auto !important;
            flex: 1 !important;
            min-width: 0 !important;
        }

        /* 手機版縮小圖片 */
        .list-img { width: 48px; height: 48px; }
        .icon-container { height: 50px; }
    }

    @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-8px); } 100% { transform: translateY(0px); } }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 邏輯與介面
# ==========================================

def get_github_repo():
    try:
        g = Github(st.secrets["github"]["token"])
        repo = g.get_repo(st.secrets["github"]["repo_name"])
        return repo
    except:
        return None

def get_data_from_github(repo):
    try:
        contents = repo.get_contents("data.json", ref=st.secrets["github"]["branch"])
        data = json.loads(contents.decoded_content.decode())
        return data, contents.sha
    except:
        return [], None

@st.cache_data(ttl=3600)
def get_image_base64(_repo, img_path):
    try:
        contents = _repo.get_contents(img_path, ref=st.secrets["github"]["branch"])
        img_data = contents.decoded_content
        b64_encoded = base64.b64encode(img_data).decode().replace("\n", "")
        mime = "image/png"
        if img_path.lower().endswith(".jpg"): mime = "image/jpeg"
        return f"data:{mime};base64,{b64_encoded}"
    except:
        return None

def upload_to_github(repo, file_bytes, path, msg):
    try:
        repo.create_file(path, msg, file_bytes, branch=st.secrets["github"]["branch"])
        return True
    except: return False

def update_json_in_github(repo, data, sha, msg):
    try:
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        if sha: repo.update_file("data.json", msg, json_str, sha, branch=st.secrets["github"]["branch"])
        else: repo.create_file("data.json", msg, json_str, branch=st.secrets["github"]["branch"])
        return True
    except: return False

# ----------------------------
# 主程式
# ----------------------------

# 頂部
st.markdown("""
    <div style="display:flex; align-items:center; border-bottom:5px solid #8b0000; padding-bottom:10px; margin-bottom:15px;">
        <div style="width:40px; height:40px; background:radial-gradient(circle at 30% 30%, #44d4ff, #005a9e); border-radius:50%; border:3px solid white; box-shadow:0 0 10px rgba(255,255,255,0.6); margin-right:15px;"></div>
        <div style="width:10px; height:10px; background:#ff5555; border-radius:50%; margin-right:5px;"></div>
        <div style="width:10px; height:10px; background:#ffcc00; border-radius:50%; margin-right:5px;"></div>
        <div style="width:10px; height:10px; background:#55ff55; border-radius:50%;"></div>
    </div>
""", unsafe_allow_html=True)

repo = get_github_repo()

if repo:
    data_list, sha = get_data_from_github(repo)
    
    if not data_list:
        st.warning("請先新增資料")
        current_item = None
    else:
        if st.session_state.selected_index >= len(data_list): st.session_state.selected_index = 0
        current_item = data_list[st.session_state.selected_index]

    # --- A. 螢幕顯示區 ---
    if current_item:
        main_img = get_image_base64(repo, current_item['img_path'])
        if not main_img: main_img = "https://via.placeholder.com/300x300/000000/30a7d7?text=Error"

        html = textwrap.dedent(f"""
            <div class="display-box">
                <div class="tech-info">
                    <div class="tech-id">ID: {current_item['id']}</div>
                    <div class="tech-name">{current_item['name']}</div>
                </div>
                <div class="glow-ring"></div>
                <img src="{main_img}" class="pokemon-img-main">
            </div>
        """)
        st.markdown(html, unsafe_allow_html=True)

        if 'audio_path' in current_item and current_item['audio_path']:
            audio_url = f"https://raw.githubusercontent.com/{st.secrets['github']['repo_name']}/{st.secrets['github']['branch']}/{current_item['audio_path']}"
            st.audio(audio_url)

    # --- B. 列表區 (點擊圖片版) ---
    st.markdown("###### ▽ 選擇目標 (SELECT)")
    
    with st.container(height=300):
        if data_list:
            cols_per_row = 4
            rows = [data_list[i:i + cols_per_row] for i in range(0, len(data_list), cols_per_row)]

            for row_items in rows:
                cols = st.columns(cols_per_row)
                
                for col, item in zip(cols, row_items):
                    with col:
                        idx = data_list.index(item)
                        active_cls = "active-border" if idx == st.session_state.selected_index else ""
                        
                        thumb = get_image_base64(repo, item['img_path'])
                        if not thumb: thumb = "https://via.placeholder.com/60"
                        
                        # 1. 顯示圖片 HTML
                        st.markdown(f"""
                        <div class="icon-container">
                            <img src="{thumb}" class="list-img {active_cls}">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 2. 透明按鈕 (覆蓋在圖片上)
                        # label 設為空白，CSS 會負責將其透明化並拉到圖片上方
                        if st.button(" ", key=f"btn_{item['id']}"):
                            st.session_state.selected_index = idx
                            st.rerun()

    # --- C. 新增資料 ---
    st.markdown("---")
    with st.expander("🛠️ 新增資料"):
        with st.form("add"):
            c1, c2 = st.columns(2)
            with c1: nid = st.text_input("編號")
            with c2: nname = st.text_input("名稱")
            nimg = st.file_uploader("圖片", type=['png','jpg'])
            naud = st.file_uploader("聲音", type=['mp3','wav','opus'])
            
            if st.form_submit_button("上傳"):
                if nid and nname and nimg:
                    if any(d['id']==nid for d in data_list): st.error("ID重複")
                    else:
                        img_path = f"pic/{nid}_{nname}.{nimg.name.split('.')[-1]}"
                        upload_to_github(repo, nimg.getvalue(), img_path, "img")
                        aud_path = ""
                        if naud:
                            aud_path = f"wav/{nid}_{nname}.{naud.name.split('.')[-1]}"
                            upload_to_github(repo, naud.getvalue(), aud_path, "aud")
                        
                        data_list.append({"id":nid, "name":nname, "img_path":img_path, "audio_path":aud_path})
                        data_list.sort(key=lambda x:x['id'])
                        update_json_in_github(repo, data_list, sha, "update")
                        st.success("成功!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("請填寫完整")
else:
    st.error("GitHub 連線失敗")