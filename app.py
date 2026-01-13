import streamlit as st
from github import Github
import json
import base64
import time
import textwrap # 關鍵：引入 textwrap 防止 HTML 縮排造成亂碼或錯誤

# ==========================================
# 1. 基礎設定與 CSS 樣式
# ==========================================
st.set_page_config(
    page_title="寶可夢科技圖鑑 V13.0",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 初始化 Session State
if 'selected_index' not in st.session_state:
    st.session_state.selected_index = 0 

# 載入 CSS
st.markdown("""
    <style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    /* 全局變數 */
    :root {
        --ui-cyan: #30a7d7;
        --ui-dark-cyan: #005a9e;
        --screen-bg: #1a1a1a;
        --card-bg: #222;
        --active-color: #ffd700;
    }

    /* 強制深色背景 */
    .stApp { background-color: #333 !important; color: white !important; }
    header, footer {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }

    /* --- 頂部裝飾條 --- */
    .top-bar {
        display: flex; align-items: center; padding-bottom: 10px;
        border-bottom: 5px solid #8b0000; margin-bottom: 15px;
    }
    .camera-lens {
        width: 45px; height: 45px;
        background: radial-gradient(circle at 30% 30%, #44d4ff, #005a9e);
        border-radius: 50%; border: 3px solid white;
        box-shadow: 0 0 10px rgba(255,255,255,0.6); margin-right: 15px;
    }
    .led { width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; border: 1px solid rgba(0,0,0,0.3); }
    .led.red { background: #ff5555; } .led.yellow { background: #ffcc00; } .led.green { background: #55ff55; }

    /* --- 上方大螢幕顯示區 --- */
    .display-box {
        background: radial-gradient(circle at center, #2a2a2a 0%, #000 100%);
        border: 2px solid #555; border-bottom: 4px solid var(--ui-cyan);
        border-radius: 10px; position: relative;
        height: 320px; width: 100%;
        overflow: hidden;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8); margin-bottom: 15px;
    }

    .tech-info { margin-bottom: 5px; text-align: center; position: relative; z-index: 20; }
    .tech-id { font-family: monospace; color: var(--ui-cyan); font-weight: bold; font-size: 1.1rem; letter-spacing: 2px;}
    .tech-name { font-size: 1.8rem; font-weight: bold; color: #fff; text-shadow: 0 0 10px var(--ui-cyan); margin-top: -5px;}

    /* --- [修改] 只保留核心光暈，移除所有旋轉圈圈 --- */
    .glow-ring {
        position: absolute; 
        top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(48, 167, 215, 0.5) 0%, transparent 70%);
        border-radius: 50%; z-index: 1; pointer-events: none;
    }
    
    .pokemon-img-main {
        position: relative; z-index: 10;
        height: 220px; width: auto; object-fit: contain;
        filter: drop-shadow(0 0 15px rgba(48, 167, 215, 0.6));
        animation: float 4s ease-in-out infinite;
    }

    /* --- 下方清單優化 (手機版適配) --- */
    .stButton button {
        width: 100%; 
        border: 1px solid #444; 
        background-color: #222;
        color: #aaa; 
        padding: 2px 0px;
        border-radius: 8px; 
        transition: all 0.2s;
        min-height: 40px;
    }
    
    .stButton button:hover {
        border-color: var(--ui-cyan); background-color: #2a2a2a;
        color: var(--ui-cyan);
    }

    .icon-container {
        display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: 5px;
    }
    
    .list-img {
        width: 55px; height: 55px; object-fit: contain;
        background: #000; border-radius: 50%; 
        border: 2px solid #555; padding: 2px;
    }

    /* 選中狀態 */
    .active-border {
        border-color: var(--active-color) !important;
        box-shadow: 0 0 10px var(--active-color);
    }

    /* --- [修改] 手機版強制四欄排列 CSS --- */
    @media (max-width: 576px) {
        /* 強制水平排列不換行 (針對 Streamlit 內部結構) */
        [data-testid="stHorizontalBlock"] {
            display: flex;
            flex-wrap: nowrap !important;
            gap: 2px !important;
        }
        
        /* 強制每個欄位寬度為 25% (一行四個) */
        [data-testid="column"] {
            flex: 0 0 25% !important;
            max-width: 25% !important;
            min-width: 0 !important;
            padding: 0 !important;
        }

        /* 縮小圖片與按鈕 */
        .list-img { width: 40px; height: 40px; margin-bottom: 2px; }
        .stButton button { font-size: 0.7rem !important; padding: 0px !important; min-height: 30px; }
        .stButton button p { font-size: 0.7rem !important; }
    }

    @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-8px); } 100% { transform: translateY(0px); } }

    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GitHub 資料處理函數
# ==========================================

def get_github_repo():
    try:
        g = Github(st.secrets["github"]["token"])
        repo = g.get_repo(st.secrets["github"]["repo_name"])
        return repo
    except Exception as e:
        st.error(f"GitHub 連線失敗: {e}")
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
        
        mime_type = "image/png"
        if img_path.lower().endswith(".jpg") or img_path.lower().endswith(".jpeg"):
            mime_type = "image/jpeg"
            
        return f"data:{mime_type};base64,{b64_encoded}"
    except Exception as e:
        return None

def upload_to_github(repo, file_bytes, path, commit_message):
    try:
        repo.create_file(path, commit_message, file_bytes, branch=st.secrets["github"]["branch"])
        return True
    except Exception as e:
        st.error(f"上傳失敗: {e}")
        return False

def update_json_in_github(repo, data, sha, commit_message):
    try:
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        if sha:
            repo.update_file("data.json", commit_message, json_str, sha, branch=st.secrets["github"]["branch"])
        else:
            repo.create_file("data.json", commit_message, json_str, branch=st.secrets["github"]["branch"])
        return True
    except Exception as e:
        st.error(f"資料更新失敗: {e}")
        return False

# ==========================================
# 3. 主程式介面
# ==========================================

st.markdown("""
    <div class="top-bar">
        <div class="camera-lens"></div>
        <div class="led red"></div>
        <div class="led yellow"></div>
        <div class="led green"></div>
        <span style="color:white; font-weight:bold; margin-left:auto; font-family:monospace;">SYSTEM V13.0</span>
    </div>
""", unsafe_allow_html=True)

repo = get_github_repo()

if repo:
    data_list, sha = get_data_from_github(repo)
    
    if not data_list:
        st.warning("資料庫是空的，請展開下方選單新增資料。")
        current_item = None
    else:
        if st.session_state.selected_index >= len(data_list):
            st.session_state.selected_index = 0
        current_item = data_list[st.session_state.selected_index]

    # --- A. 上方螢幕顯示區 ---
    if current_item:
        main_img_src = get_image_base64(repo, current_item['img_path'])
        if not main_img_src:
            main_img_src = "https://via.placeholder.com/300x300/000000/30a7d7?text=No+Image"

        # 使用 textwrap.dedent 安全地處理 HTML 縮排，防止亂碼
        html_code = textwrap.dedent(f"""
            <div class="display-box">
                <div class="tech-info">
                    <div class="tech-id">ID: {current_item['id']}</div>
                    <div class="tech-name">{current_item['name']}</div>
                </div>
                <div class="glow-ring"></div>
                <img src="{main_img_src}" class="pokemon-img-main">
            </div>
        """)
        st.markdown(html_code, unsafe_allow_html=True)

        if 'audio_path' in current_item and current_item['audio_path']:
            audio_url = f"https://raw.githubusercontent.com/{st.secrets['github']['repo_name']}/{st.secrets['github']['branch']}/{current_item['audio_path']}"
            st.audio(audio_url)
    else:
        st.markdown("""<div class="display-box" style="color:white;">WAITING FOR DATA...</div>""", unsafe_allow_html=True)

    # --- B. 下方清單 (極簡圖示版) ---
    st.markdown("###### ▽ 選擇目標 (SELECT)")
    
    # 這裡我們手動計算每四個一組，建立 Grid
    with st.container(height=300):
        if data_list:
            cols_per_row = 4
            rows = [data_list[i:i + cols_per_row] for i in range(0, len(data_list), cols_per_row)]

            for row_items in rows:
                cols = st.columns(cols_per_row)
                
                # 如果這行不滿4個，cols 長度會是 4，row_items 可能小於 4
                # zip 會自動處理到最短的長度
                for col, item in zip(cols, row_items):
                    with col:
                        original_idx = data_list.index(item)
                        
                        # 圖片樣式 (選中時加框)
                        img_class = "list-img active-border" if original_idx == st.session_state.selected_index else "list-img"
                        
                        thumb_src = get_image_base64(repo, item['img_path'])
                        if not thumb_src: thumb_src = "https://via.placeholder.com/60"
                        
                        # 1. 顯示圖片 (HTML)
                        st.markdown(f"""
                        <div class="icon-container">
                            <img src="{thumb_src}" class="{img_class}">
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 2. 顯示按鈕 (只顯示編號 No.XXXX)
                        # key 必須唯一
                        if st.button(f"No.{item['id']}", key=f"btn_{item['id']}"):
                            st.session_state.selected_index = original_idx
                            st.rerun()

    # --- C. 管理員新增區 ---
    st.markdown("---")
    with st.expander("🛠️ 管理員模式：新增寶可夢"):
        with st.form("add_pokemon_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_id = st.text_input("編號 (例: 0001)", max_chars=4)
            with c2:
                new_name = st.text_input("名稱 (例: 噴火龍)")
            
            new_img = st.file_uploader("圖片 (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
            new_audio = st.file_uploader("叫聲 (MP3/WAV)", type=['mp3', 'wav', 'opus'])
            
            submitted = st.form_submit_button("確認上傳 (UPLOAD)")
            
            if submitted:
                if not new_id or not new_name or not new_img:
                    st.warning("⚠️ 請填寫完整資訊")
                else:
                    if any(d['id'] == new_id for d in data_list):
                        st.error(f"編號 {new_id} 已經存在！")
                    else:
                        progress_bar = st.progress(0, text="連線中...")
                        try:
                            progress_bar.progress(30, text="上傳圖片...")
                            img_ext = new_img.name.split('.')[-1]
                            img_path = f"pic/{new_id}_{new_name}.{img_ext}"
                            upload_to_github(repo, new_img.getvalue(), img_path, f"Add img {new_id}")
                            
                            audio_path = ""
                            if new_audio:
                                progress_bar.progress(60, text="上傳聲音...")
                                audio_ext = new_audio.name.split('.')[-1]
                                audio_path = f"wav/{new_id}_{new_name}.{audio_ext}"
                                upload_to_github(repo, new_audio.getvalue(), audio_path, f"Add audio {new_id}")
                            
                            progress_bar.progress(80, text="更新資料庫...")
                            new_entry = {
                                "id": new_id,
                                "name": new_name,
                                "img_path": img_path,
                                "audio_path": audio_path
                            }
                            data_list.append(new_entry)
                            data_list.sort(key=lambda x: x['id'])
                            
                            update_json_in_github(repo, data_list, sha, f"Add entry {new_id}")
                            
                            progress_bar.progress(100, text="完成！")
                            st.success(f"{new_name} 已登錄！")
                            time.sleep(1)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"發生錯誤: {e}")

else:
    st.error("GitHub 連線失敗，請檢查 secrets.toml 設定。")