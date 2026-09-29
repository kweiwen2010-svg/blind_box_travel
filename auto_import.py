import json
import os
import google.generativeai as genai
import streamlit as st
from supabase import create_client, Client

# ==================== 安全讀取金鑰 ====================
# 優先嘗試從 Streamlit secrets 讀取，若無則從系統環境變數讀取
try:
  SUPABASE_URL = st.secrets["SUPABASE_URL"]
  SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
  GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
  SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
  SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
  GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 確保金鑰已載入
if not SUPABASE_URL or not SUPABASE_KEY or not GEMINI_API_KEY:
  print(
      "❌ 錯誤：找不到 Supabase 或 Gemini 金鑰！請確保已設定環境變數或 .streamlit/secrets.toml"
  )
  exit(1)

# 初始化 Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 初始化 Gemini（強制將金鑰編碼為 ascii，過濾掉任何非法字元）
clean_gemini_key = GEMINI_API_KEY.encode("ascii", "ignore").decode("ascii")
genai.configure(api_key=clean_gemini_key)

# 使用穩定且支援的模型版本
model = genai.GenerativeModel("gemini-3.6-flash")


def get_existing_spot_names():
  """取得目前資料庫已存在的景點名稱，避免重複生成"""
  try:
    response = supabase.table("locations").select("name").execute()
    if response.data:
      return [item["name"] for item in response.data]
  except Exception as e:
    print(f"⚠️ 讀取現有資料庫失敗: {e}")
  return []


def fetch_ai_spots(existing_names):
  """呼叫 Gemini 擴充 10 個冷門、奇特景點（包含特點與美食）"""
  prompt = f"""
    你是一個台灣深度旅遊與美食專家。請幫我推薦 10 個台灣各縣市冷門、名字奇特、幽默、或有強烈地方都市傳說的私房景點。
    
    【重要限制】
    以下景點已經存在資料庫中，絕對不能重複生成：
    {existing_names}
    
    每個景點必須包含以下欄位：
    - name: 景點名稱
    - city: 所屬縣市（例如：嘉義市、台南市、苗栗縣）
    - lat: 緯度 (float)
    - lng: 經度 (float)
    - category: 類別（例如：🟢 奇特地名, 👻 傳說廢墟, ⛰️ 自然秘境, ⛩️ 神祕宮廟）
    - story: 有趣的由來故事或都市傳說
    - features: 核心景點特點（例如：全台獨特的奇特地貌、廢墟風網美打卡點）
    - food: 周邊在地美食（例如：在地人必吃火雞肉飯、巷弄手工豆花）
    - fortune: 一句幽默的冒險籤詩
    
    請嚴格以純 JSON 格式回傳陣列（Array），不要包覆在 markdown ```json 程式碼區塊中，確保可以直接被 json.loads() 解析。
    """

  try:
    response = model.generate_content(prompt)
    text = response.text.strip()
    # 清理可能被包覆的 markdown 標記
    if text.startswith("```json"):
      text = text[7:]
    if text.endswith("```"):
      text = text[:-3]
    text = text.strip()

    spots = json.loads(text)
    return spots
  except Exception as e:
    print(f"❌ Gemini 解析或生成失敗: {e}")
    if "response" in locals():
      print(f"原始回應內容：\n{response.text}")
    return []


def main():
  print("正在檢查現有資料庫...")
  existing_names = get_existing_spot_names()
  print(f"目前資料庫共有 {len(existing_names)} 個景點。")

  print("正在呼叫 Gemini 擴充新景點（包含特點與美食）...")
  new_spots = fetch_ai_spots(existing_names)

  if not new_spots:
    print("⚠️ 沒有成功取得新景net點。")
    return

  success_count = 0
  for spot in new_spots:
    try:
      data = {
          "name": spot["name"],
          "city": spot["city"],
          "lat": float(spot["lat"]),
          "lng": float(spot["lng"]),
          "category": spot.get("category", "🟢 奇特地名"),
          "story": spot.get("story", ""),
          "features": spot.get("features", ""),
          "food": spot.get("food", ""),
          "fortune": spot.get("fortune", ""),
      }
      res = supabase.table("locations").insert(data).execute()
      print(f"✅ 成功新增：【{spot['city']}】{spot['name']}")
      success_count += 1
    except Exception as e:
      print(f"❌ 寫入資料庫失敗 [{spot.get('name', '未知')}]: {e}")

  print(f"\n🎉 批次匯入完成！本次成功新增 {success_count} 個新景點。")


if __name__ == "__main__":
  main()