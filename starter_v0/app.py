"""Streamlit UI cho Research Agent (bonus).

Chạy:
    cd starter_v0
    source .venv/bin/activate
    streamlit run app.py

UI cho phép chat nhiều lượt với agent, hiển thị rõ từng tool call + tool result,
và lưu transcript JSON giống chat.py để nộp bài.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

# Tái dùng đúng vòng lặp model->tool đã kiểm thử trong chat.py (không trùng lặp logic).
from chat import run_model_tool_loop, trim_history, write_transcript, now_iso, safe_slug

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")

# ---------------- Green theme (CSS tùy chỉnh) ----------------
st.markdown(
    """
    <style>
      :root { --leaf:#16a34a; --leaf-dark:#15803d; --leaf-soft:#dcf5e6; }
      .stApp { background: linear-gradient(180deg,#f3faf5 0%,#eaf7ef 100%); }
      /* Tiêu đề chính */
      h1 { color: var(--leaf-dark) !important; font-weight: 800 !important; }
      .block-container { padding-top: 2.2rem; }
      /* Nút bấm */
      .stButton > button {
        background: var(--leaf); color:#fff; border:0; border-radius:10px;
        font-weight:600; transition: all .15s ease;
      }
      .stButton > button:hover { background: var(--leaf-dark); transform: translateY(-1px); }
      /* Bong bóng chat */
      [data-testid="stChatMessage"] {
        border-radius:14px; padding:.4rem .7rem; margin-bottom:.4rem;
        border:1px solid var(--leaf-soft);
        box-shadow:0 1px 4px rgba(22,163,74,.08);
      }
      /* Expander tool call */
      [data-testid="stExpander"] details {
        border:1px solid var(--leaf-soft) !important; border-radius:12px;
        background:#ffffffcc;
      }
      [data-testid="stExpander"] summary { color:var(--leaf-dark); font-weight:600; }
      /* Caption + sidebar */
      [data-testid="stCaptionContainer"] { color: var(--leaf-dark) !important; }
      section[data-testid="stSidebar"] { background:#e8f6ee; border-right:1px solid var(--leaf-soft); }
      section[data-testid="stSidebar"] h2 { color:var(--leaf-dark) !important; }
      /* Ô nhập chat */
      [data-testid="stChatInput"] textarea { border-radius:12px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def build_runtime(provider_name: str, version: str) -> dict[str, Any]:
    """Khởi tạo provider + tool declarations một lần cho mỗi (provider, version)."""
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    declarations = load_tool_declarations(tools_path)
    provider = make_provider(provider_name)
    artifact_version = build_artifact_version(version, ARTIFACTS_DIR / "system_prompt.md", tools_path)
    return {
        "system_prompt": system_prompt,
        "openai_tools": to_openai_tools(declarations),
        "provider": provider,
        "model": getattr(provider, "default_model", None),
        "artifact_version": artifact_version.artifact_version,
        "tool_count": len(declarations),
    }


# ---------------- Sidebar config ----------------
with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.text_input("Version label", value="v3")
    history_window = st.slider("History window (cặp lượt)", 1, 10, 5)
    max_tool_rounds = st.slider("Max tool rounds", 1, 6, 4)
    save_transcript = st.checkbox("Lưu transcript JSON", value=True)
    if st.button("🗑️ Xoá hội thoại"):
        st.session_state.clear()
        st.rerun()

try:
    rt = build_runtime(provider_name, version)
except Exception as exc:  # provider key / dependency lỗi
    st.error(f"Không khởi tạo được provider `{provider_name}`: {type(exc).__name__}: {exc}")
    st.stop()

st.title("🔎 Research Agent")
st.caption(f"artifact_version = `{rt['artifact_version']}`  ·  {rt['tool_count']} tools  ·  provider = {provider_name}")

# ---------------- Session state ----------------
if "history" not in st.session_state:
    st.session_state.history = []          # list[{role, content}] cho ngữ cảnh model
if "display" not in st.session_state:
    st.session_state.display = []          # list[{role, text, tool_events}] để render
if "transcript" not in st.session_state:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = "_".join([safe_slug(version), safe_slug(provider_name), "ui", ts])
    st.session_state.transcript = {
        "transcript_id": tid,
        "artifact_version": rt["artifact_version"],
        "provider": provider_name,
        "ui": "streamlit",
        "created_at": now_iso(),
        "turns": [],
    }
    st.session_state.transcript_path = ROOT / "transcripts" / f"{tid}.transcript.json"


def render_tool_events(events: list[dict[str, Any]]) -> None:
    for ev in events:
        with st.expander(f"🔧 {ev.get('tool')}({json.dumps(ev.get('args', {}), ensure_ascii=False)})"):
            st.json(ev.get("result", {}))


# ---------------- Render lịch sử ----------------
for msg in st.session_state.display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])
        if msg.get("tool_events"):
            render_tool_events(msg["tool_events"])

# ---------------- Nhập liệu ----------------
user_text = st.chat_input("Nhập yêu cầu nghiên cứu...")
if user_text:
    st.session_state.display.append({"role": "user", "text": user_text, "tool_events": []})
    with st.chat_message("user"):
        st.markdown(user_text)

    messages = [
        {"role": "system", "content": rt["system_prompt"]},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý..."):
            try:
                result = run_model_tool_loop(
                    provider=rt["provider"],
                    messages=messages,
                    tools=rt["openai_tools"],
                    model=rt["model"],
                    max_tool_rounds=max_tool_rounds,
                )
                assistant_text = result["assistant_text"] or "(agent không trả về nội dung)"
                status = result["status"]
                tool_events = result["tool_events"]
            except Exception as exc:
                assistant_text = f"**Lỗi provider:** {type(exc).__name__}: {exc}"
                status = "provider_error"
                tool_events = []
                result = {"status": status, "rounds": [], "tool_events": []}

        if status == "waiting_for_user":
            st.info("Agent đang chờ bạn bổ sung thông tin (clarify).")
        st.markdown(assistant_text)
        if tool_events:
            render_tool_events(tool_events)

    st.session_state.display.append({"role": "assistant", "text": assistant_text, "tool_events": tool_events})
    st.session_state.history.append({"role": "user", "content": user_text})
    st.session_state.history.append({"role": "assistant", "content": assistant_text})

    # Lưu transcript JSON để nộp bài
    st.session_state.transcript["turns"].append({
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "user": user_text,
        "status": status,
        "assistant_text": assistant_text,
        "rounds": result.get("rounds", []),
        "tool_events": tool_events,
        "at": now_iso(),
    })
    if save_transcript:
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)
        st.caption(f"💾 Transcript: `{st.session_state.transcript_path.name}`")
