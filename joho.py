import streamlit as st
from streamlit_calendar import calendar
import datetime
import json
import os
import uuid
from datetime import datetime as dt
import pytz

st.set_page_config(page_title="クリックで予定入力カレンダー", layout="wide")
st.title("📅 サッカー部予定カレンダー")

DATA_FILE = "events.json"
JST = pytz.timezone("Asia/Tokyo")  # 東京タイムゾーン

# -------------------------
# ヘルパ：読み込み & id付与
# -------------------------
def load_events_with_ids():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = []
    if isinstance(data, dict):
        for k, v in data.items():
            events.append({"title": v, "start": k, "end": k})
    elif isinstance(data, list):
        events = data
    else:
        return []

    changed = False
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if "id" not in ev:
            ev["id"] = str(uuid.uuid4())
            changed = True
    if changed:
        save_events(events)
    return events

def save_events(events):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

# -------------------------
# ヘルパ：クリック情報取得（JSTに変換）
# -------------------------
def extract_clicked_info(clicked_raw):
    if not clicked_raw:
        return {}
    if isinstance(clicked_raw, dict) and "event" in clicked_raw and isinstance(clicked_raw["event"], dict):
        ev = clicked_raw["event"]
    else:
        ev = clicked_raw if isinstance(clicked_raw, dict) else {}

    info = {}
    if "id" in ev:
        info["id"] = ev.get("id")
    info["title"] = ev.get("title") or ev.get("text") or ev.get("name")

    raw_start = ev.get("start") or ev.get("startStr") or ev.get("date") or ev.get("dateStr")
    if raw_start:
        try:
            dt_obj = dt.fromisoformat(str(raw_start))
            dt_obj = dt_obj.astimezone(JST)
            s = dt_obj.strftime("%Y-%m-%d %H:%M")
        except Exception:
            s = str(raw_start)[:16]
        info["start"] = s

    return info

# -------------------------
# 初期ロード
# -------------------------
events = load_events_with_ids()

# -------------------------
# カレンダー設定
# -------------------------
calendar_options = {
    "initialView": "dayGridMonth",
    "editable": True,
    "selectable": True,
    "locale": "ja",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek",
    },
}

# -------------------------
# レイアウト
# -------------------------
col1, col2 = st.columns([3, 1])

# -------------------------
# カレンダー表示
# -------------------------
with col1:
    state = calendar(events=events, options=calendar_options, key="calendar")

# -------------------------
# クリック取得
# -------------------------
clicked_raw = None
if state:
    for key in ("eventClick", "clicked", "eventClickInfo", "clickedEvent"):
        if key in state and state[key]:
            clicked_raw = state[key]
            break

clicked_info = extract_clicked_info(clicked_raw)

if clicked_info.get("id"):
    st.session_state["selected_id"] = clicked_info["id"]
    st.session_state["selected_title"] = clicked_info.get("title", "")
    st.session_state["selected_start"] = clicked_info.get("start", "")
else:
    if clicked_info.get("title") and clicked_info.get("start"):
        st.session_state["selected_id"] = None
        st.session_state["selected_title"] = clicked_info["title"]
        st.session_state["selected_start"] = clicked_info["start"]

selected_id = st.session_state.get("selected_id", None)
selected_title = st.session_state.get("selected_title", None)
selected_start = st.session_state.get("selected_start", None)

# -------------------------
# 右パネル：削除
# -------------------------
with col2:
    st.subheader("📝 選択中の予定")
    if selected_title:
        st.markdown(f"**タイトル：** {selected_title}")
        st.markdown(f"**日付：** {selected_start or '（未取得）'}")

        delete_pressed = st.button("❌ この予定を削除する")
        if delete_pressed:
            deleted = False
            if selected_id:
                events = [e for e in events if e.get("id") != selected_id]
                deleted = True
            else:
                candidates = [
                    idx for idx, e in enumerate(events)
                    if e.get("title","") == selected_title and e.get("start","") == selected_start
                ]
                if len(candidates) == 1:
                    del events[candidates[0]]
                    deleted = True

            if deleted:
                save_events(events)
                st.session_state.clear()
                # ボタン押下直後だけ rerun
                st.experimental_rerun()
            else:
                st.warning("一致する予定が見つかりませんでした（タイトル＋日付）。")
    else:
        st.info("カレンダー上の予定をクリックするとここに表示されます。")

# -------------------------
# 日付クリックで追加（JST）
# -------------------------
clicked_date = None
if state and "dateClick" in state and state["dateClick"]:
    dc = state["dateClick"]
    clicked_date = dc.get("date") or dc.get("start") or dc.get("startStr")
elif state and "select" in state and state["select"]:
    sel = state["select"]
    clicked_date = sel.get("start") or sel.get("startStr")

if clicked_date:
    try:
        dt_obj = dt.fromisoformat(str(clicked_date))
        dt_obj = dt_obj.astimezone(JST)
        normalized_clicked = dt_obj.strftime("%Y-%m-%d %H:%M")
    except Exception:
        normalized_clicked = str(clicked_date)[:16]

    st.info(f"🗓 {normalized_clicked} の予定を追加します。")
    with st.form("add_event"):
        title = st.text_input("予定を入力してください")
        submitted = st.form_submit_button("保存")

    if submitted and title:
        new_event = {
            "id": str(uuid.uuid4()),
            "title": title,
            "start": normalized_clicked,
            "end": normalized_clicked,
        }
        events.append(new_event)
        save_events(events)
        st.success("保存しました！")
        st.experimental_rerun()  # ここでのみ呼ぶ

# -------------------------
# 全削除
# -------------------------
delete_all_pressed = st.button("🗑 予定をすべて削除")
if delete_all_pressed:
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.success("全削除しました。")
    st.experimental_rerun()  # ここでのみ呼ぶ
