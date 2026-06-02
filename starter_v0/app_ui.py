"""
Flask web UI for the Research Agent.
Run: python app_ui.py --provider openrouter --version v3
Then open: http://localhost:5000
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, Response

from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

app = Flask(__name__)

# ── Global session state (single-user dev mode) ──────────────────────────────
_state: dict[str, Any] = {
    "provider": None,
    "openai_tools": None,
    "system_prompt": "",
    "model": None,
    "artifact_version": None,
    "history": [],
    "history_window": 6,
    "max_tool_rounds": 4,
    # transcript
    "transcript": {},
    "transcript_path": None,
    "turn_index": 0,
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_transcript(path: Path, transcript: dict[str, Any]) -> None:
    transcript["updated_at"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def json_text(value: Any, *, max_chars: int | None = None) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def trim_history(history: list[dict], window: int) -> list[dict]:
    if window <= 0:
        return []
    return history[-(window * 2):]


def execute_tool_call(call: ToolCall) -> dict[str, Any]:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {"tool": call.name, "args": call.args,
                "result": {"error": "unknown_tool", "message": f"No implementation for {call.name}"}}
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def assistant_tool_message(text: str | None, calls: list[ToolCall]) -> dict:
    summary = [{"name": c.name, "args": c.args} for c in calls]
    return {
        "role": "assistant",
        "content": (text or "Calling tools…") + f"\n\nTOOL_CALLS_JSON:\n{json_text(summary)}",
    }


def tool_results_message(events: list[dict]) -> dict:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json_text(events, max_chars=24000)}\n\n"
            "Use only these tool results. Answer the user directly with cited sources when available."
        ),
    }


def run_agent(user_text: str) -> dict[str, Any]:
    """Run the agent for one user turn. Returns a dict with text + tool_events."""
    state = _state
    state["turn_index"] += 1
    turn_index = state["turn_index"]

    messages = [
        {"role": "system", "content": state["system_prompt"]},
        *trim_history(state["history"], state["history_window"]),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "tool_events": [],
    }

    tool_events: list[dict] = []
    working = list(messages)

    for _ in range(state["max_tool_rounds"]):
        response = state["provider"].complete(
            working, state["openai_tools"], model=state["model"], temperature=0.0
        )
        calls = response.tool_calls

        if not calls:
            state["history"].append({"role": "user", "content": user_text})
            state["history"].append({"role": "assistant", "content": response.text or ""})
            turn_record.update({"status": "answered", "assistant_text": response.text or "", "tool_events": tool_events, "ended_at": now_iso()})
            state["transcript"].setdefault("turns", []).append(turn_record)
            write_transcript(state["transcript_path"], state["transcript"])
            return {"text": response.text or "", "tool_events": tool_events}

        working.append(assistant_tool_message(response.text, calls))
        non_clarify: list[dict] = []

        for call in calls:
            event = execute_tool_call(call)
            tool_events.append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                state["history"].append({"role": "user", "content": user_text})
                state["history"].append({"role": "assistant", "content": question})
                turn_record.update({"status": "waiting_for_user", "assistant_text": question, "tool_events": tool_events, "ended_at": now_iso()})
                state["transcript"].setdefault("turns", []).append(turn_record)
                write_transcript(state["transcript_path"], state["transcript"])
                return {"text": question, "tool_events": tool_events}

            non_clarify.append(event)

        working.append(tool_results_message(non_clarify))

    state["history"].append({"role": "user", "content": user_text})
    fallback = "Đã vượt quá số vòng tool. Vui lòng thử lại."
    state["history"].append({"role": "assistant", "content": fallback})
    turn_record.update({"status": "max_tool_rounds", "assistant_text": fallback, "tool_events": tool_events, "ended_at": now_iso()})
    state["transcript"].setdefault("turns", []).append(turn_record)
    write_transcript(state["transcript_path"], state["transcript"])
    return {"text": fallback, "tool_events": tool_events}


# ── Helper: scan runs / transcripts ──────────────────────────────────────────

def _load_run_summaries() -> list[dict[str, Any]]:
    """Scan runs/*.json and return lightweight summaries."""
    runs_dir = ROOT / "runs"
    results = []
    if not runs_dir.exists():
        return results
    for f in sorted(runs_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            s = data.get("summary", {})
            results.append({
                "file": f.name,
                "run_id": data.get("run_id", f.stem),
                "version": data.get("version", ""),
                "suite": data.get("suite", ""),
                "provider": data.get("provider", ""),
                "model": data.get("model", ""),
                "generated_at": data.get("generated_at", ""),
                "total_cases": s.get("total_cases", 0),
                "passed_cases": s.get("passed_cases", 0),
                "case_accuracy": s.get("case_accuracy", 0),
                "tool_routing_accuracy": s.get("tool_routing_accuracy", 0),
                "argument_accuracy": s.get("argument_accuracy", 0),
                "failure_counts": s.get("failure_counts", {}),
            })
        except Exception:
            pass
    return results


def _load_transcript_summaries() -> list[dict[str, Any]]:
    """Scan transcripts/*.transcript.json and return lightweight summaries."""
    tr_dir = ROOT / "transcripts"
    results = []
    if not tr_dir.exists():
        return results
    for f in sorted(tr_dir.glob("*.transcript.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            turns = data.get("turns", [])
            tool_count = sum(len(t.get("tool_events", [])) for t in turns)
            results.append({
                "file": f.name,
                "transcript_id": data.get("transcript_id", f.stem),
                "version": data.get("version", ""),
                "provider": data.get("provider", ""),
                "model": data.get("model", ""),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "total_turns": len(turns),
                "total_tool_calls": tool_count,
                "turns": [
                    {
                        "turn_index": t.get("turn_index", i + 1),
                        "user": (t.get("user") or "")[:120],
                        "assistant_text": (t.get("assistant_text") or "")[:200],
                        "status": t.get("status", ""),
                        "started_at": t.get("started_at", ""),
                        "tool_calls": [e.get("tool") for e in t.get("tool_events", [])],
                    }
                    for i, t in enumerate(turns)
                ],
            })
        except Exception:
            pass
    return results


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/logs")
def logs_page():
    return render_template("logs.html",
                           version=_state.get("artifact_version", ""),
                           model=_state.get("model", ""))


@app.route("/api/runs")
def api_runs():
    return jsonify(_load_run_summaries())


@app.route("/api/transcripts")
def api_transcripts():
    return jsonify(_load_transcript_summaries())


@app.route("/api/runs/<filename>")
def api_run_detail(filename: str):
    path = ROOT / "runs" / filename
    if not path.exists() or not path.suffix == ".json":
        return jsonify({"error": "not found"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.route("/api/transcripts/<filename>")
def api_transcript_detail(filename: str):
    path = ROOT / "transcripts" / filename
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.route("/")
def index():
    return render_template(
        "index.html",
        version=_state.get("artifact_version", ""),
        model=_state.get("model", ""),
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_text = (data.get("message") or "").strip()
    if not user_text:
        return jsonify({"error": "empty message"}), 400

    if user_text in {"/clear", "/reset"}:
        _state["history"].clear()
        _state["turn_index"] = 0
        return jsonify({"text": "🗑️ Lịch sử chat đã được xóa.", "tool_events": []})

    try:
        result = run_agent(user_text)
        result["transcript_path"] = str(_state["transcript_path"])
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc), "text": f"Lỗi: {exc}", "tool_events": []}), 500


@app.route("/transcript")
def get_transcript():
    """Trả về toàn bộ transcript dạng JSON."""
    return jsonify(_state.get("transcript", {}))


@app.route("/transcript/download")
def download_transcript():
    """Download transcript file."""
    path: Path = _state.get("transcript_path")
    if not path or not path.exists():
        return jsonify({"error": "No transcript yet"}), 404
    content = path.read_text(encoding="utf-8")
    return Response(
        content,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@app.route("/status")
def status():
    return jsonify({
        "ok": True,
        "version": str(_state.get("artifact_version", "")),
        "model": _state.get("model", ""),
        "history_turns": len(_state["history"]) // 2,
        "transcript_path": str(_state.get("transcript_path", "")),
        "transcript_turns": len(_state.get("transcript", {}).get("turns", [])),
    })


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Research Agent Web UI")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True)
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--history-window", type=int, default=6)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(args.tools)
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(args.provider)
    selected_model = args.model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    safe_version = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.version.strip())
    transcript_id = f"ui_{safe_version}_{args.provider}_{timestamp}"
    transcripts_dir = ROOT / "transcripts"
    transcript_path = transcripts_dir / f"{transcript_id}.transcript.json"

    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": args.provider,
        "model": selected_model,
        "system_prompt": str(args.system_prompt),
        "tools": str(args.tools),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    _state.update({
        "provider": provider,
        "openai_tools": openai_tools,
        "system_prompt": system_prompt,
        "model": selected_model,
        "artifact_version": artifact_version.artifact_version,
        "history": [],
        "history_window": args.history_window,
        "max_tool_rounds": args.max_tool_rounds,
        "transcript": transcript,
        "transcript_path": transcript_path,
        "turn_index": 0,
    })

    print(f"  Research Agent UI")
    print(f"  artifact_version : {artifact_version.artifact_version}")
    print(f"  model            : {selected_model}")
    print(f"  transcript       : {transcript_path}")
    print(f"  URL              : http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
