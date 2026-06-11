import os
import json

FEEDBACK_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../rlhf_feedback.json"))
def load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        return json.loads(content)
    except Exception:
        try:
            os.remove(FEEDBACK_FILE)
        except Exception:
            pass
        return []

def to_ascii(text):
    if not isinstance(text, str):
        return ""
    return text.encode("ascii", errors="ignore").decode("ascii")

def save_feedback(entry):
    safe = {
        "timestamp": float(entry.get("timestamp")),
        "question": to_ascii(entry.get("question", "")),
        "answer": to_ascii(entry.get("answer", ""))[:500],
        "score": int(entry.get("score", 1)),
        "comment": to_ascii(entry.get("comment", ""))
    }
    data = load_feedback()
    data.append(safe)
    try:
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
    except Exception as e:
        print(f"[RLHF save error] {e}")
