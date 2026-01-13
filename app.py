import streamlit as st
from github import Github
import json
import time
import base64

# ==========================================
# 1. 基礎設定與 CSS 樣式 (官方特效版)
# ==========================================
st.set_page_config(
    page_title="寶可夢科技圖鑑 V10.0",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 載入 CSS
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

    /* App 背景設為深灰 */
    .stApp { background-color: #333; }

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
    
    /* 1. 螢幕外框 */
    .display-box {
        background: radial-gradient(circle at center, #2a2a2a 0%, #000 100%);
        border: 2px solid #555;
        border-bottom: 4px solid var(--ui-cyan);
        border-radius: 15px;
        position: relative;
        height: 380px; /* 固定高度，確保特效空間 */
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
    }

    /* 2. 背景旋轉光環 (外圈虛線) */
    .ring-outer {
        position: absolute;
        width: 300px; height: 300px;
        border: 1px dashed rgba(48, 167, 215, 0.4);
        border-radius: 50%;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        animation: spin 30s linear infinite;
        z-index: 1;
    }

    /* 3. 背景旋轉光環 (內圈實線) */
    .ring-inner {
        position: absolute;
        width: 260px; height: 260px;
        border: 2px solid rgba(48, 167, 215, 0.6);
        border-top-color: transparent; 
        border-bottom-color: transparent;
        border-radius: 50%;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        animation: spin 15s linear infinite reverse;
        z-index: 2;
        box-shadow: 0 0 15px rgba(48, 167, 215, 0.2);
    }

    /* 4. 中央發光核心 */
    .core-glow {
        position: absolute;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(48, 167, 215, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        z-index: 1;
    }

    /* 5. 寶可夢圖片 (懸浮特效) */
    .poke-img-style {
        position: relative;
        z-index: 10; 
        height: 240px;
        max-width: 90%;
        object-fit: contain;
        filter: drop-shadow(0 15px 15px rgba(0,0,0,0.6));
        animation: float 3s ease-in-out infinite;
    }

    /* 6. 資訊文字 (左上角) */
    .info-overlay {
        position: absolute;
        top: 15px; left: 20px;
        z-index: 20;
        text-align: left;
    }
    .tech-id { font-family: 'Courier New', monospace; color: var(--ui-cyan); font-size: 1.3rem; font-weight: bold; letter-spacing: 2px; }
    .tech-name { color: white; font-size: 1.6rem; font-weight: bold; text-shadow: 0 0 8px var(--ui-cyan); margin-top: -5px; }

    /* 動畫定義 */
    @keyframes spin {
        from { transform: translate(-50%, -50%) rotate(0deg); }
        to { transform: translate(-50%, -50%) rotate(360deg); }
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
        token = st.secrets["github"]["token"]
        repo_name = st.secrets["github"]["repo_name"]
        g = Github(token)
        return g.get_repo(repo_name)
    except Exception as e:
        st.error(f"GitHub 連線失敗，請檢查 secrets.toml 設定。\n錯誤訊息: {e}")
        return None

def get_data_from_github(repo):
    """讀取 data.json"""
    try:
        branch = st.secrets["github"]["branch"]
        contents = repo.get_contents("data.json", ref=branch)
        data = json.loads(contents.decoded_content.decode())
        return data, contents.sha
    except:
        return [], None

def get_base64_content(repo, path):
    """
    讀取檔案並轉為 Base64 字串
    (這一步是關鍵：讓私人 Repo 的圖片和聲音也能在前端顯示)
    """
    try:
        branch = st.secrets["github"]["branch"]
        file_content = repo.get_contents(path, ref=branch)
        # 轉成 Base64
        b64_str = base64.b64encode(file_content.decoded_content).decode()
        
        # 判斷 MIME Type
        ext = path.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg']: mime = 'image/jpeg'
        elif ext == 'png': mime = 'image/png'
        elif ext == 'gif': mime = 'image/gif'
        elif ext == 'mp3': mime = 'audio/mpeg'
        elif ext == 'wav': mime = 'audio/wav'
        elif ext == 'opus': mime = 'audio/ogg' # 寬鬆處理
        else: mime = 'application/octet-stream'
        
        return f"data:{mime};base64,{b64_str}"
    except Exception as e:
        # st.warning(f"無法讀取檔案 {path}: {e}")
        return None

def upload_to_github(repo, file_bytes, path, commit_message):
    try:
        branch = st.secrets["github"]["branch"]
        repo.create_file(path, commit_message, file_bytes, branch=branch)
        return True
    except Exception as e:
        st.error(f"上傳失敗 ({path}): {e}")
        return False

def update_json_in_github(repo, data, sha, commit_message):
    try:
        branch = st.secrets["github"]["branch"]
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        if sha:
            repo.update_file("data.json", commit_message, json_str, sha, branch=branch)
        else:
            repo.create_file("data.json", commit_message, json_str, branch=branch)
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

# === Tab 1: 圖鑑瀏覽 ===
with tab1:
    if repo:
        data_list, _ = get_data_from_github(repo)
        
        if not data_list:
            st.info("資料庫目前是空的，請切換到「新增資料」分頁添加第一隻寶可夢！")
        else:
            # 下拉選單
            options = {f"{item['id']} {item['name']}": item for item in data_list}
            selected_key = st.selectbox("選擇目標", list(options.keys()), label_visibility="collapsed")
            
            if selected_key:
                item = options[selected_key]
                
                # 取得圖片 (Base64)
                img_src = get_base64_content(repo, item['img_path'])
                if not img_src:
                    # 替代圖片
                    img_src = "https://upload.wikimedia.org/wikipedia/commons/5/53/Pok%C3%A9_Ball_icon.svg"

                # 🔥 顯示特效區塊 (HTML/CSS) 🔥
                st.markdown(f"""
                    <div class="display-box">
                        <div class="info-overlay">
                            <div class="tech-id">ID: {item['id']}</div>
                            <div class="tech-name">{item['name']}</div>
                        </div>

                        <div class="ring-outer"></div>
                        <div class="ring-inner"></div>
                        <div class="core-glow"></div>

                        <img src="{img_src}" class="poke-img-style">
                    </div>
                """, unsafe_allow_html=True)

                # 聲音播放
                if 'audio_path' in item and item['audio_path']:
                    audio_src = get_base64_content(repo, item['audio_path'])
                    if audio_src:
                        st.audio(audio_src)

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