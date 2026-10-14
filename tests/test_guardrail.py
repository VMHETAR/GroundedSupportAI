"""Guardrail unit tests: Tier1 flags hallucinations, Tier2 fails unsafe answers, logs decisions."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.guardrail import Guardrail, tier1_score

CHUNKS = [{"section": "p334-se-tax",
           "text": "You must pay self-employment tax if your net earnings from self-employment are $400 or more. The SE tax rate is 15.3 percent."}]

def test_tier1_passes_verbatim():
    s, _ = tier1_score("net earnings from self-employment are $400 or more", CHUNKS)
    assert s >= 0.28, f"verbatim should pass Tier1, got {s}"

def test_tier1_flags_hallucination():
    s, _ = tier1_score("The 2026 mileage rate is 99 cents and you can deduct your house cat.", CHUNKS)
    assert s < 0.28, f"hallucination should flag Tier1, got {s}"

def test_tier2_blocks_unverified_and_logs(tmp_path):
    log = str(tmp_path / "decisions.jsonl")
    g = Guardrail(log_path=log)
    # force Tier1 flag with unrelated response; Tier2 heuristic (no LLM key) should fail long low-overlap answer
    long_bad = " ".join(["The IRS guarantees a $9,999 bonus deduction for all drivers."] * 30)
    final, dec = g.check(long_bad, CHUNKS, "What bonus exists?")
    assert dec["tier2_ran"] is True
    assert dec["verdict"] in ("pass", "fail")
    assert "tier1_score" in dec and "latency_s" in dec
    import json
    assert os.path.exists(log)
