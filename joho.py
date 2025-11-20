import json
import datetime
import streamlit as st
from streamlit_oauth import OAuth2Component

# ========== Google OAuth 設定 ==========
client_id = "あなたのGoogleClientID"
client_secret = "あなたのGoogleClientSecret"
redirect_uri = "http://localhost:8501"

authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://oauth2.googleapis.com/token"

oauth = OAuth2Component(
    client_id,
    client_secret,
    authorization_base_url,
    token_url,
    redirect_uri,
    {"scope": "openid email profile"},
)

# ========== OAuth2ログイン ==========
st.title("🔐 Googleログイン → カレンダーアプリ")

if "token" not in st.session_state:
    st.session_state.token = None

if st.session_state.token is None:
    result = oauth.authorize_button("Googleでログイン", key="google")
    if result and "token" in result:
        st.session_state.token = result["token"]

if st.session_state.token is None:
    st.stop()

# ログイン成功
st.success("ログインしました！")
user_info = oauth.get_user_info(st.session_state.token)
st.write(f"こんにちは、**{user_info.get('name')}** さん")

# ========== 予定データを読み書きする関数 ==========
EVENT_FILE = "events.json"

def load_events():
    try:
        with open(EVENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_events(events):
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

events = load_events()

# ========== カレンダー表示 ==========
st.header("📅 カレンダーに予定を追加する")

today = datetime.date.today()
year = st.sidebar.selectbox("年", list(range(2020, 2031)), index=year := list(range(2020,2031)).index(today.year))
month = st.sidebar.selectbox("月", list(range(1, 13)), index=today.month - 1)

first_day = datetime.date(year, month, 1)
start_weekday = first_day.weekday()
days = (datetime.date(year + (month // 12), ((month % 12) + 1), 1) - datetime.timedelta(days=1)).day

# 表形式でカレンダーを描画
import calendar
cal = calendar.Calendar(firstweekday=0)

st.subheader(f"{year}年 {month}月")

clicked_date = None

# カレンダー描画
for week in cal.monthdatescalendar(year, month):
    cols = st.columns(7)
    for i, day in enumerate(week):
        label = str(day.day)
        if day.month != month:
            cols[i].write(" ")

        else:
            # ボタンで日付選択
            if cols[i].button(label, key=f"{day}"):
                clicked_date = day

            # 予定があれば表示
            date_key = str(day)
            if date_key in events:
                cols[i].write(f"📝 {events[date_key]['title']}")

# ========== 日付をクリックしたら予定入力フォーム ==========
if clicked_date:
    st.subheader(f"📌 {clicked_date} の予定を入力")
    title = st.text_input("予定タイトル")
    memo = st.text_area("メモ")

    if st.button("保存"):
        events[str(clicked_date)] = {
            "title": title,
            "memo": memo
        }
        save_events(events)
        st.success("保存しました！")
        st.experimental_rerun()

# ========== 保存された予定一覧 ==========
st.subheader("🗂 登録済みの予定一覧")

for date_str, info in sorted(events.items()):
    st.write(f"**{date_str}**：{info['title']}")
    st.caption(info["memo"])
