import random
import urllib.parse
import streamlit as st
from supabase import create_client, Client

# ==================== 頁面基本設定 ====================
st.set_page_config(
    page_title="盲盒旅遊與吃貨冒險", page_icon="🎯", layout="centered"
)

# ==================== 安全讀取金鑰 ====================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()


# ==================== 從資料庫載入景點 ====================
@st.cache_data(ttl=60)
def load_locations():
  try:
    response = supabase.table("locations").select("*").execute()
    return response.data if response.data else []
  except Exception as e:
    st.error(f"無法載入資料庫景點: {e}")
    return []


locations = load_locations()

# ==================== 介面主體 ====================
st.title("🎯 盲盒旅遊與吃貨冒險 App")
st.markdown("抽一個神祕景點，帶上你的胃，馬上出發！")

if not locations:
  st.warning(
      "⚠️ 資料庫目前沒有景點，請先執行 `auto_import.py` 匯入景點資料！"
  )
else:
  st.info(f"📦 目前盲盒資料庫共有 **{len(locations)}** 個精彩私房景點！")

  # 初始化 Session State 存放當前抽中的景點
  if "selected_spot" not in st.session_state:
    st.session_state.selected_spot = None

  # 抽盲盒按鈕
  if st.button("🎲 隨機盲抽一個神祕景點！", type="primary", use_container_width=True):
    st.session_state.selected_spot = random.choice(locations)

  # 如果已經抽中景點，展示詳細卡片
  spot = st.session_state.selected_spot
  if spot:
    st.divider()
    st.subheader(f"🎯 恭喜抽中：{spot.get('name', '未命名景點')}")
    st.caption(
        f"📍 所在地：**{spot.get('city', '未分類')}** | 類別：**{spot.get('category', '探索景點')}**"
    )

    # 左右分欄展示：特點與美食（加上嚴格防呆，徹底排除 None）
    col1, col2 = st.columns(2)

    with col1:
      st.markdown("### ✨ 景點特點")
      features = spot.get("features")
      if not features or str(features).strip() in ["None", "null", ""]:
        st.info("這是一個充滿神祕色彩的在地私房景點！")
      else:
        st.info(features)

    with col2:
      st.markdown("### 🍜 在地美食")
      food = spot.get("food")
      if not food or str(food).strip() in ["None", "null", ""]:
        st.success("探索周邊巷弄，發掘在地隱藏版小吃！")
      else:
        st.success(food)

    # 神祕傳說與籤詩
    with st.container(border=True):
      st.markdown("### 📜 冒險傳說與故事")
      story = spot.get("story")
      if not story or str(story).strip() in ["None", "null", ""]:
        st.write("這個神祕的景點還沒有流傳出故事，等待你親自去發掘...")
      else:
        st.write(story)

      st.markdown("### 🔮 今日冒險籤詩")
      fortune = spot.get("fortune")
      if not fortune or str(fortune).strip() in ["None", "null", ""]:
        st.warning("勇往直前，必有收穫！")
      else:
        st.warning(fortune)

   # Google Maps 一鍵導航按鈕（純網址字串，絕不夾帶 markdown）
    lat = spot.get("lat")
    lng = spot.get("lng")
    spot_name = spot.get("name", "")

    if lat and lng:
      maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot_name)}&query_place_id=&center={lat},{lng}"
    else:
      maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot_name)}"

    st.link_button(
        "🗺️ 一鍵 Google 導航出發", maps_url, use_container_width=True
    )
  # 側邊欄：檢視所有景點清單
  with st.sidebar:
    st.header("📋 現有景點清單")
    if st.checkbox("顯示資料庫所有景點"):
      for item in locations:
        st.markdown(f"- **{item.get('name', '未命名')}** ({item.get('city', '')})")