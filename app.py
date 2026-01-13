import streamlit as st
from github import Github
import json
import base64
import time

# --- 1. 設定頁面配置 ---
st.set_page_config(
    page_title="寶可夢科技圖鑑 V10.0",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. 載入 CSS (保留原本的科技風格) ---
st.markdown("""
    <style>
    /* 引入字體 */
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    /* 全局變數 */
    :root {
        --pokedex-red: #dc0a2d;
        --ui-cyan: #30a7d7;
        --screen-bg: #111;
        --text-color: #f0f0f0;
    }

    /* 背景與主體 */
    .stApp {
        background-color: #333;
    }
    
    /* 模擬 Pokedex 外框 */
    .main-container {
        border: 10px solid var(--pokedex-red);
        border-radius: 15px;
        background-color: var(--pokedex-red);
        padding: 10px;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
    }

    /* 頂部裝飾 */
    .top-bar {
        display: flex;
        align-items: center;
        padding-bottom: 10px;
        border-bottom: 5px solid #8b0000;
        margin-bottom: 15px;
    }
    .camera-lens {
        width: 40px; height: 40px;
        background: radial-gradient(circle at 30% 30%, #44d4ff, #005a9e);
        border-radius: 50%; border: 3px solid white;
        box-shadow: 0 0 10px rgba(255,255,255,0.5);
        margin-right: 15px;
    }
    .led { width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; border: 1px solid rgba(0,0,0,0.2); }
    .led.red { background: #ff5555; }
    .led.yellow { background: #ffcc00; }
    .led.green { background: #55ff55; }

    /* 螢幕區域 */
    .screen-area {
        background-color: #dedede;
        border-radius: 10px;
        border: 2px solid #555;
        padding: 15px;
        min-height: 400px;
    }

    /* 顯示區 (深色) */
    .display-box {
        background: radial-gradient(circle at center, #222 0%, var(--screen-bg) 100%);
        border-bottom: 3px solid var(--ui-cyan);
        padding: 20px;
        text-align: center;
        border-radius: 5px 5px 0 0;
        position: relative;
        overflow: hidden;
    }

    /* 科技感文字 */
    .tech-id { font-family: 'Courier New', monospace; color: var(--ui-cyan); font-weight: bold; font-size: 1.2rem; }
    .tech-name { font-size: 1.8rem; font-weight: bold; color: #fff; text-shadow: 0 0 10px var(--ui-cyan); }

    /* 按鈕樣式 */
    .stButton button {
        background-color: var(--ui-cyan);
        color: #000;
        font-weight: bold;
        border-radius: 20px;
        border: none;
        box-shadow: 0 0 10px rgba(48, 167, 215, 0.5);
    }
    .stButton button:hover {
        background-color: #fff;
        box-shadow: 0 0 20px #fff;
    }
    
    /* 隱藏 Streamlit 預設 header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. GitHub 連接功能 ---
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
        # 如果檔案不存在，回傳空清單
        return [], None

def upload_to_github(repo, file_bytes, path, commit_message):
    """上傳檔案 (圖片或聲音)"""
    try:
        repo.create_file(path, commit_message, file_bytes, branch=st.secrets["github"]["branch"])
        return True
    except Exception as e:
        st.error(f"上傳失敗 ({path}): {e}")
        return False

def update_json_in_github(repo, data, sha, commit_message):
    """更新 data.json"""
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

# --- 4. 主程式邏輯 ---

# 頂部裝飾 (HTML)
st.markdown("""
    <div class="top-bar">
        <div class="camera-lens"></div>
        <div class="led red"></div>
        <div class="led yellow"></div>
        <div class="led green"></div>
        <span style="color:white; font-weight:bold; margin-left:auto;">SYSTEM V10.0</span>
    </div>
""", unsafe_allow_html=True)

# 分頁選單
tab1, tab2 = st.tabs(["📂 圖鑑瀏覽", "➕ 新增資料"])

repo = get_github_repo()

# === Tab 1: 圖鑑瀏覽 ===
with tab1:
    if repo:
        data_list, _ = get_data_from_github(repo)
        
        if not data_list:
            st.info("資料庫目前是空的，請到「新增資料」分頁添加！")
        else:
            # 選擇器
            options = {f"{item['id']} {item['name']}": item for item in data_list}
            selected_label = st.selectbox("選擇目標", list(options.keys()))
            
            if selected_label:
                item = options[selected_label]
                
                # 顯示區域
                st.markdown(f"""
                    <div class="display-box">
                        <div class="tech-id">{item['id']}</div>
                        <div class="tech-name">{item['name']}</div>
                    </div>
                """, unsafe_allow_html=True)

                # 圖片 (直接從 GitHub Raw URL 讀取)
                # 為了避免快取問題，我們加上 timestamp
                img_url = f"https://raw.githubusercontent.com/{st.secrets['github']['repo_name']}/{st.secrets['github']['branch']}/{item['img_path']}"
                st.image(img_url, use_container_width=True)

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
            
        new_img = st.file_uploader("上傳圖片", type=['png', 'jpg', 'jpeg'])
        new_audio = st.file_uploader("上傳叫聲 (選填)", type=['mp3', 'wav', 'opus'])
        
        submitted = st.form_submit_button("啟動傳輸協定 (上傳)")
        
        if submitted:
            if not new_id or not new_name or not new_img:
                st.warning("⚠️ 編號、名稱與圖片為必填欄位")
            else:
                progress_text = "連線 GitHub 資料庫中..."
                my_bar = st.progress(0, text=progress_text)
                
                # 1. 取得現有資料
                current_data, sha = get_data_from_github(repo)
                
                # 檢查 ID 是否重複
                if any(d['id'] == new_id for d in current_data):
                    st.error(f"編號 {new_id} 已經存在！")
                else:
                    try:
                        # 2. 上傳圖片
                        my_bar.progress(30, text="上傳影像資料...")
                        img_ext = new_img.name.split('.')[-1]
                        img_path = f"pic/{new_id}_{new_name}.{img_ext}"
                        upload_to_github(repo, new_img.getvalue(), img_path, f"Add image for {new_id}")
                        
                        # 3. 上傳聲音 (如果有)
                        audio_path = ""
                        if new_audio:
                            my_bar.progress(60, text="上傳聲波資料...")
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
                        # 根據 ID 排序
                        current_data.sort(key=lambda x: x['id'])
                        
                        update_json_in_github(repo, current_data, sha, f"Add entry {new_id}")
                        
                        my_bar.progress(100, text="傳輸完成！")
                        st.success(f"✅ {new_name} 已成功登錄！請切換回「圖鑑瀏覽」查看。")
                        time.sleep(2)
                        st.rerun() # 重新整理頁面
                        
                    except Exception as e:
                        st.error(f"發生未知錯誤: {e}")