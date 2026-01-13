import streamlit as st
from github import Github
import json
import base64
import time

# ==========================================
# 1. 基礎設定與 CSS 樣式
# ==========================================
st.set_page_config(
    page_title="寶可夢科技圖鑑 V10.0",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 載入官方風格 CSS (含旋轉光環與懸浮特效)
st.markdown("""
    <style>
    /* 引入圖標字體 */
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    /* 全局變數 */
    :root {
        --ui-cyan: #30a7d7;
        --ui-dark-cyan: #005a9e;
        --screen-bg: #1a1a1a;
        --pokedex-red: #dc0a2d;
    }

    /* 強制將 App 背景設為深黑色 */
    .stApp { 
        background-color: #333 !important; 
        color: white !important;
    }

    /* 隱藏 Streamlit 預設 Header/Footer */
    header, footer {visibility: hidden;}

    /* --- 頂部裝飾條 --- */
    .top-bar {
        display: flex; align-items: center; padding-bottom: 15px;
        border-bottom: 5px solid #8b0000; margin-bottom: 20px;
    }
    .camera-lens {
        width: 50px; height: 50px;
        background: radial-gradient(circle at 30% 30%, #44d4ff, #005a9e);
        border-radius: 50%; border: 3px solid white;
        box-shadow: 0 0 15px rgba(255,255,255,0.6); margin-right: 20px;
    }
    .led { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; border: 1px solid rgba(0,0,0,0.3); }
    .led.red { background: #ff5555; } 
    .led.yellow { background: #ffcc00; } 
    .led.green { background: #55ff55; }

    /* --- 🔥 核心顯示區：模擬官方圖鑑特效 🔥 --- */
    
    /* 1. 顯示外框 */
    .display-box {
        background: #222;
        border: 2px solid #555;
        border-bottom: 3px solid var(--ui-cyan);
        padding: 15px;
        border-radius: 10px;
        position: relative;
        overflow: hidden;
    }

    /* 2. 科技感文字資訊 */
    .tech-info { margin-bottom: 15px; text-align: center; position: relative; z-index: 20; }
    .tech-id { font-family: 'Courier New', monospace; color: var(--ui-cyan); font-weight: bold; font-size: 1.2rem; letter-spacing: 2px;}
    .tech-name { font-size: 2rem; font-weight: bold; color: #fff; text-shadow: 0 0 10px var(--ui-cyan); margin-top: -5px;}

    /* 3. 特效容器：負責疊加所有圖層 */
    .tech-display-container {
        position: relative;
        width: 100%;
        height: 320px; /* 固定高度 */
        background: radial-gradient(circle at center, #2a2a2a 0%, #000 100%);
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
    }

    /* 4. 底層：發光核心 (藍色光暈) */
    .glow-ring {
        position: absolute;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(48, 167, 215, 0.6) 0%, transparent 70%);
        border-radius: 50%;
        z-index: 1;
        box-shadow: 0 0 20px rgba(48, 167, 215, 0.4);
    }

    /* 5. 中層：旋轉科技圈 (外圈虛線) */
    .rotating-ring {
        position: absolute;
        width: 260px; height: 260px;
        border: 2px dashed rgba(48, 167, 215, 0.5); /* 虛線 */
        border-radius: 50%;
        animation: spin 30s linear infinite;
        z-index: 2;
    }
    
    /* 內圈實線 */
    .rotating-ring-inner {
        position: absolute;
        width: 230px; height: 230px;
        border: 2px solid rgba(48, 167, 215, 0.3); /* 實線 */
        border-top-color: transparent; /* 缺口效果 */
        border-radius: 50%;
        animation: spin 20s linear infinite reverse;
        z-index: 2;
    }

    /* 6. 上層：寶可夢圖片本體 */
    .pokemon-img-styled {
        position: relative;
        z-index: 10;
        height: 85%;
        width: auto;
        max-width: 90%;
        object-fit: contain;
        filter: drop-shadow(0 10px 15px rgba(48, 167, 215, 0.5));
        animation: float 4s ease-in-out infinite;
    }

    /* 動畫定義 */
    @keyframes spin {
        100% { transform: rotate(360deg); }
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
        100% { transform: translateY(0px); }
    }

    /* 按鈕樣式優化 */
    .stButton button {
        background-color: var(--ui-cyan); color: #000;
        font-weight: bold; border-radius: 20px; border: none;
        box-shadow: 0 0 10px rgba(48, 167, 215, 0.5);
        width: 100%;
    }
    .stButton button:hover { background-color: #fff; box-shadow: 0 0 15px #fff; }
    
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GitHub 連線與資料處理函數
# ==========================================

def get_github_repo():
    """連接到 GitHub Repo"""
    try:
        g = Github(st.secrets["github"]["token"])
        repo = g.get_repo(st.secrets["github"]["repo_name"])
        return repo
    except Exception as e:
        st.error(f"GitHub 連線失敗: {e}")
        return None

def get_data_from_github(repo):
    """讀取 data.json"""
    try:
        contents = repo.get_contents("data.json", ref=st.secrets["github"]["branch"])
        data = json.loads(contents.decoded_content.decode())
        return data, contents.sha
    except:
        return [], None

@st.cache_data(ttl=3600)
def get_image_base64(_repo, img_path):
    """取得圖片並轉為 Base64 (支援私人 Repo)"""
    try:
        contents = _repo.get_contents(img_path, ref=st.secrets["github"]["branch"])
        img_data = contents.decoded_content
        # 轉為 Base64 並強制移除換行符號 (解決亂碼關鍵)
        b64_encoded = base64.b64encode(img_data).decode().replace("\n", "")
        
        # 判斷 MIME Type
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
        st.error(f"上傳失敗 ({path}): {e}")
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
        st.error(f"資料庫更新失敗: {e}")
        return False

# ==========================================
# 3. 主程式介面邏輯
# ==========================================

# 頂部裝飾 HTML
st.markdown("""
    <div class="top-bar">
        <div class="camera-lens"></div>
        <div class="led red"></div>
        <div class="led yellow"></div>
        <div class="led green"></div>
        <span style="color:white; font-weight:bold; margin-left:auto; font-family:monospace;">SYSTEM V10.0</span>
    </div>
""", unsafe_allow_html=True)

repo = get_github_repo()
tab1, tab2 = st.tabs(["📂 圖鑑瀏覽", "➕ 新增資料"])

# === Tab 1: 圖鑑瀏覽 (無 textwrap 版，防止報錯) ===
with tab1:
    if repo:
        data_list, _ = get_data_from_github(repo)
        
        if not data_list:
            st.info("資料庫目前是空的，請到「新增資料」分頁添加！")
        else:
            # 選擇器
            options = {f"{item['id']} {item['name']}": item for item in data_list}
            selected_label = st.selectbox("選擇寶可夢", list(options.keys()), label_visibility="collapsed")
            
            if selected_label:
                item = options[selected_label]

                # 1. 取得圖片 Base64
                img_src = get_image_base64(repo, item['img_path'])
                if not img_src:
                    # 預設圖片 (精靈球)
                    img_src = "https://upload.wikimedia.org/wikipedia/commons/5/53/Pok%C3%A9_Ball_icon.svg"

                # 2. 組合 HTML 結構
                # ⚠️ 注意：為了避免縮排造成的亂碼，這裡的 HTML 字串全部「靠左對齊」，看起來雖亂但能保證執行。
                html_code = f"""
<div class="display-box">
<div class="tech-info">
<div class="tech-id">ID: {item['id']}</div>
<div class="tech-name">{item['name']}</div>
</div>
<div class="tech-display-container">
<div class="glow-ring"></div>
<div class="rotating-ring"></div>
<div class="rotating-ring-inner"></div>
<img src="{img_src}" class="pokemon-img-styled">
</div>
</div>
"""
                st.markdown(html_code, unsafe_allow_html=True)

                # 音效
                if 'audio_path' in item and item['audio_path']:
                    audio_url = f"https://raw.githubusercontent.com/{st.secrets['github']['repo_name']}/{st.secrets['github']['branch']}/{item['audio_path']}"
                    st.audio(audio_url)

# === Tab 2: 新增資料 ===
with tab2:
    st.markdown("### 📥 登錄新生物資料")
    
    with st.form("add_pokemon_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_id = st.text_input("編號 (例如: 0001)", max_chars=4)
        with col2:
            new_name = st.text_input("名稱 (例如: 妙蛙種子)")
            
        new_img = st.file_uploader("上傳圖片 (建議去背 PNG)", type=['png', 'jpg', 'jpeg'])
        new_audio = st.file_uploader("上傳叫聲 (選填)", type=['mp3', 'wav', 'opus'])
        
        submitted = st.form_submit_button("啟動傳輸協定 (上傳)")
        
        if submitted:
            if not repo:
                st.error("GitHub 連線異常。")
            elif not new_id or not new_name or not new_img:
                st.warning("⚠️ 編號、名稱與圖片為必填欄位")
            else:
                progress_text = "連線 GitHub 資料庫中..."
                my_bar = st.progress(0, text=progress_text)
                
                # 1. 取得現有資料
                current_data, sha = get_data_from_github(repo)
                if any(d['id'] == new_id for d in current_data):
                    st.error(f"錯誤：編號 {new_id} 已經存在於圖鑑中！")
                    my_bar.empty()
                else:
                    try:
                        # 2. 上傳圖片
                        my_bar.progress(30, text="正在上傳影像資料...")
                        img_ext = new_img.name.split('.')[-1]
                        img_path = f"pic/{new_id}_{new_name}.{img_ext}"
                        upload_to_github(repo, new_img.getvalue(), img_path, f"Add image for {new_id}")
                        
                        # 3. 上傳聲音 (如果有)
                        audio_path = ""
                        if new_audio:
                            my_bar.progress(60, text="正在上傳聲波資料...")
                            audio_ext = new_audio.name.split('.')[-1]
                            audio_path = f"wav/{new_id}_{new_name}.{audio_ext}"
                            upload_to_github(repo, new_audio.getvalue(), audio_path, f"Add audio for {new_id}")
                        
                        # 4. 更新 JSON
                        my_bar.progress(80, text="寫入系統索引...")
                        new_entry = {
                            "id": new_id,
                            "name": new_name,
                            "img_path": img_path,
                            "audio_path": audio_path
                        }
                        current_data.append(new_entry)
                        current_data.sort(key=lambda x: x['id'])
                        
                        update_json_in_github(repo, current_data, sha, f"Add entry {new_id}")
                        
                        my_bar.progress(100, text="傳輸完成！")
                        st.success(f"✅ {new_name} 已成功登錄！")
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"發生未知錯誤: {e}")