"""Promptfoo exec provider: reads JSON {question, history} on stdin, prints bot answer."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import load_config
from src.bot import RAGBot
from src.guardrail import Guardrail

def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw) if raw.strip() else {}
    except Exception:
        req = {}
    prompt = req.get("prompt", req.get("question", ""))
    history = req.get("history", [])
    cfg = load_config()
    bot = RAGBot(cfg)
    guard = Guardrail(cfg)
    out = bot.answer(history + [{"role": "user", "content": prompt}])
    hist_txt = "\n".join(f"{m['role']}: {m['content']}" for m in (history + [{"role": "user", "content": prompt}]))
    final, _ = guard.check(out["response"], out["chunks"], hist_txt)
    print(final)

if __name__ == "__main__":
    main()
