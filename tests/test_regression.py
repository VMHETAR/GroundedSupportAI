"""Pytest regression: runs eval subset and fails if quality drops below baseline.

Baseline stored in eval/baseline.json: {hallucination_rate_max, refusal_accuracy_min,
judge_pass_rate_min, p95_latency_max}. Any prompt/threshold change should run:
  .venv/bin/pytest tests/test_regression.py -q
Promptfoo (promptfooconfig.yaml) calls the same path via python for prompt-level testing.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_regression_full():
    from src.config import load_config
    from src.run_eval import run_config, summarize
    from src.bot import RAGBot
    from src.guardrail import Guardrail
    cfg = load_config()
    base_path = cfg["eval"]["baseline"]
    assert os.path.exists(base_path), f"missing baseline {base_path}; run src/run_eval.py first"
    baseline = json.load(open(base_path))
    items = [json.loads(l) for l in open(cfg["eval"]["eval_set"]) if l.strip()]
    bot = RAGBot(cfg)
    guard = Guardrail(cfg)
    # full Tier1+2 config is the release gate
    rows = run_config("tier1+2", bot, guard, items, "tier1+2")
    s = summarize(rows)
    print("current:", s)
    print("baseline:", baseline)
    assert s["hallucination_rate"] <= baseline["hallucination_rate_max"] + 1e-9, \
        f"hallucination_rate {s['hallucination_rate']} > baseline max {baseline['hallucination_rate_max']}"
    assert s["refusal_accuracy"] >= baseline["refusal_accuracy_min"] - 1e-9, \
        f"refusal_accuracy {s['refusal_accuracy']} < baseline min {baseline['refusal_accuracy_min']}"
    assert s["judge_pass_rate"] >= baseline["judge_pass_rate_min"] - 1e-9, \
        f"judge_pass_rate {s['judge_pass_rate']} < baseline min {baseline['judge_pass_rate_min']}"
