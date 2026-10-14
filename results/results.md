# Eval results

Independent reimplementation (IRS Pub 334/587 excerpts). Hallucination rate = judge-fail / answerable. Refusal accuracy = correctly-refused-and-judge-pass / unanswerable. Latency = end-to-end per question (retrieve+generate[+guardrail]).

| config | n | hallucination_rate | refusal_accuracy | judge_pass_rate | p50 latency (s) | p95 latency (s) |
|---|---:|---:|---:|---:|---:|---:|
| no guardrail | 44 | 0.111 | 1.0 | 0.909 | 0.03 | 0.049 |
| Tier 1 only | 44 | 0.111 | 1.0 | 0.909 | 0.034 | 0.045 |
| Tier 1 + Tier 2 | 44 | 0.111 | 1.0 | 0.909 | 0.042 | 0.063 |

_Backend: extractive-fallback (no OMNIROUTER_API_KEY set); judge backend: heuristic_
