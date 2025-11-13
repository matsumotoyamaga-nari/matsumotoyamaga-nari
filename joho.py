
import streamlit as st
from streamlit_calendar import calendar
import json
import os

DATA_FILE = "events.json"

def load_events():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_events(events):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

st.set_page_config(page_title="予定カレンダー", layout="centered")
st.title("📅 カレンダー予定アプリ")

events = load_events()

calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": True,
    "locale": "ja",
    "height": 650,
}

state = calendar(events=events, options=calendar_options, key="calendar")

# 日付をクリックしたら入力欄表示
if state.get("select_info"):
    date = state["select_info"]["start"][:10]
    st.session_state["date"] = date

if "date" in st.session_state:
    st.markdown("---")
    st.subheader(f"🗓 {st.session_state['date']} の予定を追加")
    title = st.text_input("予定タイトル")
    if st.button("💾 保存"):
        new_event = {
            "title": title if title else "予定",
            "start": st.session_state["date"],
            "end": st.session_state["date"],
        }
        events.append(new_event)
        save_events(events)
        st.success("保存しました！")
        st.session_state.pop("date")
        st.experimental_rerun()
