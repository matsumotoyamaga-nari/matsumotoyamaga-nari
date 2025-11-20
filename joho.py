import streamlit as st
from streamlit_calendar import calendar
import datetime
import json
import os
import uuid
from datetime import datetime as dt

st.set_page_config(page_title="クリックで予定入力カレンダー", layout="wide")
st.title("📅 クリックで予定を追加できるカレンダー")

DATA_FILE = "events.json"

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
# ヘルパ：クリック情報取得
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
        s = str(raw_start)
        if "T" in s:
            s = s.split("T")[0]
        else:
            try:
                s = dt.fromisoformat(s).date().isoformat()
            except Exception:
                s = s[:10]
        info["start"] = s

    return info

# -------------------------
# 初期ロード
# -------------------------
events = load_events_with_ids()

# -------------------------
# レイアウト
# -------------------------
col1, col2 = st.columns([3, 1])

# -------------------------
# 右パネル：年・月選択
# -------------------------
with col2:
    st.subheader("🗓 年月選択")

    today = datetime.date.today()
    year_list = list(range(2020, 2031))
    year_index = year_list.index(today.year)
    year = st.selectbox("年", year_list, index=year_index)

    month_list = list(range(1, 13))
    month_index = month_list.index(today.month)
    month = st.selectbox("月", month_list, index=month_index)

# -------------------------
# カレンダー設定
# -------------------------
calendar_options = {
    "initialView": "dayGridMonth",
    "editable": True,
    "selectable": True,
    "locale": "ja",
    "initialDate": f"{year}-{month:02d}-01",  # 選択年月で初期表示
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek",
    },
}

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

        if st.button("❌ この予定を削除する"):
            if selected_id:
                new_events = [e for e in events if e.get("id") != selected_id]
                save_events(new_events)
                st.session_state.clear()
                st.experimental_rerun()
            else:
                candidates = []
                for idx, e in enumerate(events):
                    ev_title = e.get("title", "")
                    ev_start = e.get("start", "")
                    s = str(ev_start)
                    if "T" in s:
                        s = s.split("T")[0]
                    else:
                        try:
                            s = dt.fromisoformat(s).date().isoformat()
                        except Exception:
                            s = s[:10]
                    if ev_title == selected_title and s == selected_start:
                        candidates.append(idx)

                if len(candidates) == 1:
                    del events[candidates[0]]
                    save_events(events)
                    st.session_state.clear()
                    st.experimental_rerun()
                else:
                    st.warning("一致する予定が見つかりませんでした（タイトル＋日付）。")
    else:
        st.info("カレンダー上の予定をクリックするとここに表示されます。")

# -------------------------
# 日付クリックで追加（時間入力なし）
# -------------------------
clicked_date = None
if state and "dateClick" in state and state["dateClick"]:
    dc = state["dateClick"]
    clicked_date = dc.get("date") or dc.get("start") or dc.get("startStr")
elif state and "select" in state and state["select"]:
    sel = state["select"]
    clicked_date = sel.get("start") or sel.get("startStr")

if clicked_date:
    cd = str(clicked_date)
    normalized_clicked = cd.split("T")[0]

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
            st.experimental_rerun()

# -------------------------
# 全削除
# -------------------------
if st.button("🗑 予定をすべて削除"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.success("全削除しました。")
    st.experimental_rerun()
