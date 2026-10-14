"""Run full eval set in 3 configs: no guardrail, Tier1 only, Tier1+Tier2.

Metrics:
- hallucination_rate = judge-fail / answerable count (lower is better)
- refusal_accuracy   = correctly-refused / unanswerable count (higher is better)
- p50/p95 latency across all questions per config
Saves results/results.json + results/results.md, appends failures to failures.md.

Usage: .venv/bin/python -m src.run_eval [--limit N] [--config all|none|tier1|tier1+2]
"""
import os, sys, json, time, re, statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import load_config
from src.bot import RAGBot
from src.guardrail import Guardrail, tier1_score
from src import eval_judge

REFUSAL_RE = re.compile(r"(can't verify|cannot verify|not in my knowledge|don't have enough|no information in the provided|human handoff|tax professional)", re.I)

def is_refusal(text):
    return bool(REFUSAL_RE.search(text or ""))

def categorize(item, response, retrieved, judge_res, guard_decision, refused):
    answerable = item["answerable"]
    expected = item.get("expected_source", [])
    hit = any(e in retrieved for e in expected) if expected else True
    if judge_res.get("pass"):
        return None  # not a failure
    if not answerable:
        if not refused:
            if guard_decision and guard_decision.get("verdict") == "pass":
                return ("guardrail false negative", "unanswerable answered instead of refused; guardrail passed it")
            return ("ungrounded generation", "answered unanswerable without refusal")
        return ("other", "judge failed a refusal (wording); check judge calibration")
    # answerable but failed
    if refused:
        if guard_decision and guard_decision.get("verdict") == "fail":
            return ("guardrail false positive", "good question refused after guardrail block; check Tier1 threshold/excerpts")
        return ("ungrounded generation", "model refused answerable question (over-cautious generation)")
    if expected and not hit:
        return ("retrieval miss", f"expected {expected} not in retrieved {retrieved}")
    if guard_decision and guard_decision.get("verdict") == "fail":
        return ("guardrail false positive", "answer blocked though judge says content was borderline")
    return ("ungrounded generation", "answer not supported by excerpts per judge")

def run_config(name, bot, guard, items, mode):
    rows = []
    for it in items:
        t0 = time.time()
        history = it.get("history", [])
        messages = history + [{"role": "user", "content": it["question"]}]
        out = bot.answer(messages)
        response, chunks = out["response"], out["chunks"]
        retrieved = [c.get("section", "") for c in chunks]
        guard_decision = None
        if mode == "tier1":
            s1, _ = tier1_score(response, chunks, guard.ww, guard.stride)
            passed = s1 >= guard.threshold
            guard_decision = {"tier1_score": round(s1, 4), "tier1_pass": passed,
                              "tier2_ran": False, "verdict": "pass" if passed else "fail"}
            if not passed:
                response = guard.fallback
        elif mode == "tier1+2":
            hist_txt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
            response, guard_decision = guard.check(response, chunks, hist_txt)
        lat = time.time() - t0
        refused = is_refusal(response)
        j = eval_judge.judge(it["question"], response, retrieved, it.get("expected_source", []),
                             it["answerable"], history="")
        rows.append({"id": it["id"], "question": it["question"], "answerable": it["answerable"],
                     "expected": it.get("expected_source", []), "retrieved": retrieved,
                     "response": response, "refused": refused, "judge": j,
                     "guard": guard_decision, "latency_s": round(lat, 3),
                     "backend": out.get("backend")})
    return rows

def summarize(rows):
    ans = [r for r in rows if r["answerable"]]
    una = [r for r in rows if not r["answerable"]]
    hall = sum(1 for r in ans if not r["judge"]["pass"]) / max(1, len(ans))
    ref_acc = sum(1 for r in una if r["refused"] and r["judge"]["pass"]) / max(1, len(una))
    # strict refusal accuracy: refused regardless of judge wording
    ref_strict = sum(1 for r in una if r["refused"]) / max(1, len(una))
    lats = sorted(r["latency_s"] for r in rows)
    def pct(p):
        if not lats:
            return 0.0
        i = min(len(lats) - 1, int(p / 100 * len(lats)))
        return round(lats[i], 3)
    pass_rate = sum(1 for r in rows if r["judge"]["pass"]) / max(1, len(rows))
    return {"n": len(rows), "n_answerable": len(ans), "n_unanswerable": len(una),
            "hallucination_rate": round(hall, 3), "refusal_accuracy": round(ref_acc, 3),
            "refusal_rate_strict": round(ref_strict, 3),
            "judge_pass_rate": round(pass_rate, 3),
            "p50_latency_s": pct(50), "p95_latency_s": pct(95)}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--config", default="all", choices=["all", "none", "tier1", "tier1+2"])
    args = ap.parse_args()
    cfg = load_config()
    items = [json.loads(l) for l in open(cfg["eval"]["eval_set"]) if l.strip()]
    if args.limit:
        items = items[:args.limit]
    bot = RAGBot(cfg)
    guard = Guardrail(cfg)
    modes = {"none": "none", "tier1": "tier1", "tier1+2": "tier1+2"}
    selected = [args.config] if args.config != "all" else ["none", "tier1", "tier1+2"]
    all_rows, summary = {}, {}
    for m in selected:
        print(f"running config: {m} ({len(items)} questions) ...")
        rows = run_config(m, bot, guard, items, modes[m])
        all_rows[m] = rows
        summary[m] = summarize(rows)
        print(f"  {summary[m]}")
    os.makedirs("results", exist_ok=True)
    with open(cfg["eval"]["results_json"], "w") as f:
        json.dump({"summary": summary, "rows": all_rows}, f, indent=2)
    # markdown table
    order = [m for m in ["none", "tier1", "tier1+2"] if m in summary]
    labels = {"none": "no guardrail", "tier1": "Tier 1 only", "tier1+2": "Tier 1 + Tier 2"}
    md = ["# Eval results", "",
          "Independent reimplementation (IRS Pub 334/587 excerpts). "
          "Hallucination rate = judge-fail / answerable. "
          "Refusal accuracy = correctly-refused-and-judge-pass / unanswerable. "
          "Latency = end-to-end per question (retrieve+generate[+guardrail]).", "",
          "| config | n | hallucination_rate | refusal_accuracy | judge_pass_rate | p50 latency (s) | p95 latency (s) |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for m in order:
        s = summary[m]
        md.append(f"| {labels[m]} | {s['n']} | {s['hallucination_rate']} | {s['refusal_accuracy']} | "
                  f"{s['judge_pass_rate']} | {s['p50_latency_s']} | {s['p95_latency_s']} |")
    md += ["", f"_Backend: {'llm' if any(r.get('backend')=='llm' for r in all_rows[order[0]]) else 'extractive-fallback (no OMNIROUTER_API_KEY set)'}; "
                 f"judge backend: {all_rows[order[0]][0]['judge'].get('backend')}_"]
    open(cfg["eval"]["results_md"], "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    # failures.md
    fail_path = cfg["eval"]["failures_md"]
    lines = ["# Failure log", "",
             "Every wrong output recorded with question, output, failure category, root cause. "
             "Categories: retrieval miss, bad chunking, ungrounded generation, "
             "guardrail false positive, guardrail false negative, other.", ""]
    from collections import Counter
    cats = Counter()
    for m in order:
        lines.append(f"## Config: {labels[m]}")
        n_fail = 0
        for r in all_rows[m]:
            cat = categorize({"answerable": r["answerable"], "expected_source": r["expected"]},
                             r["response"], r["retrieved"], r["judge"], r["guard"], r["refused"])
            if cat:
                n_fail += 1
                cats[(m, cat[0])] += 1
                lines += [f"### {r['id']} ({'answerable' if r['answerable'] else 'unanswerable'})",
                          f"**Q:** {r['question']}",
                          f"**Expected:** {r['expected']} | **Retrieved:** {r['retrieved']}",
                          f"**Output:** {r['response'][:800]}",
                          f"**Judge:** {json.dumps(r['judge'])}",
                          f"**Guard:** {json.dumps(r['guard'])}",
                          f"**Failure category:** {cat[0]}",
                          f"**Root cause:** {cat[1]}", ""]
        if n_fail == 0:
            lines.append("No failures.")
            lines.append("")
    lines += ["## Summary (counts by config x category)", ""]
    for (m, c), n in sorted(cats.items()):
        lines.append(f"- {m} x {c}: {n}")
    if not cats:
        lines.append("- none")
    open(fail_path, "w").write("\n".join(lines) + "\n")
    print(f"wrote {cfg['eval']['results_json']}, {cfg['eval']['results_md']}, {fail_path}")

if __name__ == "__main__":
    main()
