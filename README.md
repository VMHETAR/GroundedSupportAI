# Dasher-style support automation — independent reimplementation (IRS corpus)

This is an **independent reimplementation of the approach** described in DoorDash's
engineering post “Path to high-quality LLM-based Dasher support automation.”
It is **not** DoorDash's system, has no DoorDash data, and makes no claim to reproduce
their production behavior. It rebuilds the same pattern (RAG bot + two-tier guardrail +
eval/regression) on a public corpus.

## 1. Corpus chosen and why

**IRS Publication 334 (Tax Guide for Small Business, 2025, for 2025 returns) excerpts +
IRS Publication 587 (Business Use of Your Home) excerpts.**
Approved scope: self-employment income/expenses plus home-office (you approved
“334 + 535 excerpts” + “Add Pub 587”).

- Public domain (U.S. federal work, 17 U.S.C. §105), versioned PDFs, stable URLs:
  `https://www.irs.gov/pub/irs-pdf/p334.pdf`, `.../p587.pdf`.
- Procedural support-like content (definitions, how-to deduct, thresholds, methods)
  analogous to Dasher contractor support (Dashers are independent contractors).
- Bounded and labelable: **245 chunks** after 1800-char / 200-overlap splitting, with
  per-section grounding labels used directly by the 44-question eval:
  `p334-business-expenses-general: 85`, `p334-business-income: 38`, `p334-se-tax: 34`,
  `p587-simplified-method: 30`, `p587-actual-expenses: 18`, `p587-home-use: 11`,
  `p587-exclusive-regular-use: 9`, `p587-principal-place: 7`,
  `p334-are-you-self-employed: 6`, `p334-car-truck: 3`, `p334-travel-meals: 2`,
  plus 1 general chunk per pub.
- Easy refusal tests: personal-tax / state / platform / immigration questions outside
  the excerpts (8 unanswerable in eval).
- Note: IRS retired Publication 535 as a standalone PDF (now a “Guide to Business
  Expense Resources” landing page); its content overlaps Pub 334 Ch.8, so Ch.8 serves
  as the expenses source. Documented in `config.yaml:27`.

Approved design decisions (you chose, I implemented): vector store **Qdrant**
(`qdrant-client`, local `./qdrant_data`, collection `irs_support`) instead of
FAISS/Chroma; generation via **`OMNIROUTER_API_KEY`** on an OpenAI-compatible
endpoint; embeddings **`sentence-transformers/all-MiniLM-L6-v2`** (384-dim);
regression harness **Promptfoo** (plus pytest gate).

## 2. Architecture

```
PDFs (irs.gov) -> src/ingest.py -> clean + chunk -> MiniLM embed -> Qdrant local
User -> bot.condense (multi-turn -> standalone query) -> Qdrant top-5
      -> prompt template (condensed + history + excerpts) -> LLMClient (single config)
      -> Tier1 sliding-window TF-IDF check -> (flag only) Tier2 LLM evaluator
      -> pass: show answer / fail: fallback + human handoff; log decision
Eval: eval/eval_set.jsonl (44) -> src/run_eval.py (3 configs) -> LLM judge rubric
      -> results/results.{json,md} + failures.md; pytest + Promptfoo regression gate
```

## 3. Component 1 — RAG support bot (`src/bot.py:1`)

- Ingest (`src/ingest.py:1`): downloads both PDFs to `data/corpus/`, extracts with
  `pypdf`, line-based section tagging via heading regexes, de-hyphenation cleanup,
  `chunk_chars: 1800`, `chunk_overlap_chars: 200` (`config.yaml:30`), embeds with
  MiniLM, upserts to Qdrant with payload `{text, source, section, title}`, and writes
  `data/chunks.jsonl`.
- Multi-turn: `RAGBot.condense` sends the last ≤8 turns to the condense model with
  “condense into one standalone query”; single-turn passes through; offline fallback
  appends prior user turns as context.
- Retrieval: embed condensed query, Qdrant cosine top-N (`retrieval.top_n: 5`,
  `config.yaml:59`).
- Prompt template (`src/bot.py:1`, `PROMPT_TEMPLATE`): condensed issue summary +
  conversation history + retrieved excerpts (`[section] text`) + question; system
  prompt restricts to excerpts only, requires citations like `[p334-car-truck]`,
  and mandates refusal + handoff when excerpts lack the answer.
- Swappable generation: everything reads `config.yaml:llm` via `src/config.py:1`;
  the only generation call sites are `src/llm_client.py:LLMClient`. Swap
  `generation_model` (default `llama3.1:8b`) in one place. Provider resolution:
  `OMNIROUTER_API_KEY`/`OMNIROUTER_BASE_URL` (default `http://localhost:20128/v1`)
  → `OPENAI_API_KEY`/`OPENAI_BASE_URL` → deterministic extractive fallback
  (verbatim top-overlap chunk quote + source, or clean refusal for out-of-scope),
  so eval runs with or without a key.

## 4. Component 2 — Two-tier guardrail (`src/guardrail.py:1`)

- Tier 1 (cheap, always runs): TF-IDF cosine between the response and sliding windows
  over retrieved chunks (`tier1_window_words: 80`, `tier1_stride_words: 40`,
  `tier1_threshold: 0.28`, `config.yaml:61`). Returns `(max_score, best_window)`;
  flags when no window clears the threshold.
- Tier 2 (only on Tier 1 flag): LLM evaluator receives response + retrieved chunks +
  conversation history and judges groundedness, coherence, policy compliance,
  returning JSON `{"pass": bool, "rationale": "..."}`. Heuristic fallback when no key:
  passes clean refusals, fails long near-zero-overlap answers.
- Gate: must pass both tiers to show; otherwise the fallback message
  (`config.yaml:65`): “I can't verify this answer against the IRS guides in my
  knowledge base, so I won't guess. Please contact a tax professional or request a
  human handoff for help with your specific situation.”
- Logging: every decision appended to `logs/guardrail_decisions.jsonl` with
  `tier1_score`, `tier1_threshold`, `tier1_pass`, `tier1_best_window`,
  `tier2_ran`, `tier2_pass`, `tier2_rationale`, `tier2_backend`, `verdict`,
  `latency_s` (+ `tier2_latency_s`), `response_preview`, `chunk_sections`.
  Current run: 44 logged decisions, Tier 2 ran on 6/44 (all clean refusals flagged by
  the lexical check, passed by Tier 2).

## 5. Component 3 — Eval and regression layer

- Eval set (`eval/eval_set.jsonl:1`): **44 questions (36 answerable + 8 unanswerable)**,
  each with `expected_source` section ids. q43–q44 are multi-turn (`history` +
  follow-up) to test condensing. Unanswerables (q35 2026 mileage rate, child credit,
  refund status, deactivation appeal, evasion advice, visa, state tax, crypto) must
  refuse. Correction made during eval: q35 first asked the 2025 mileage rate — which
  **is** in Pub 334 (70¢/mile) — while labeled unanswerable; fixed to the 2026 rate.
- Judge (`src/eval_judge.py:1`): LLM rubric scoring 1–5 on retrieval correctness,
  groundedness, relevance, language consistency + `pass/fail` (pass needs
  groundedness≥4 and relevance≥4; unanswerable passes only on refusal+handoff).
  Heuristic fallback offline (retrieval hit + word-overlap ≥0.2 + refusal check).
- Calibration (`eval/calibration_examples.json:1`, `src/calibrate.py:1`): 5 hand-labeled
  examples (2 correct, 1 fabricated-rate fail, 1 correct refusal, 1 methods).
  Run `.venv/bin/python -m src.calibrate` — current agreement **5/5**. To relabel:
  edit the `human` blocks, adjust thresholds in `src/eval_judge.py`, rerun.
- Regression: `tests/test_regression.py:1` (pytest) runs the full Tier 1+2 eval and
  fails if hallucination/refusal/pass-rate drops below `eval/baseline.json:1`
  (`hallucination_rate_max: 0.111`, `refusal_accuracy_min: 1.0`,
  `judge_pass_rate_min: 0.909`); Promptfoo path via `promptfooconfig.yaml:1` +
  `scripts/promptfoo_provider.py:1` + `eval/prompt_template.txt:1`
  (`promptfoo eval` after `npm install -g promptfoo`).

## 6. Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.ingest          # download PDFs, chunk, index Qdrant
# optional LLM generation/eval (else extractive fallback):
export OMNIROUTER_API_KEY=...
# export OMNIROUTER_BASE_URL=http://localhost:20128/v1
.venv/bin/python -m src.run_eval       # 44 Q x 3 configs -> results/ + failures.md
.venv/bin/python -m src.calibrate      # judge vs 5 hand labels (5/5)
.venv/bin/python -m pytest -q          # regression gate (4 passed)
# promptfoo (optional, needs npm): promptfoo eval
```

Single-query / guardrail demo:

```bash
.venv/bin/python -c "from src.bot import RAGBot; from src.guardrail import Guardrail;
b=RAGBot(); o=b.answer([{'role':'user','content':'Who must pay self-employment tax?'}]);
print(o['response'][:500]); print(Guardrail().check(o['response'], o['chunks'])[1])"
```

## 7. Measurements (required)

`results/results.md:1` is generated by `src/run_eval.py:1`. Current offline run
(extractive fallback, heuristic judge — no `OMNIROUTER_API_KEY` set):

| config | n | hallucination_rate | refusal_accuracy | judge_pass_rate | p50 latency (s) | p95 latency (s) |
|---|---:|---:|---:|---:|---:|---:|
| no guardrail | 44 | 0.111 | 1.0 | 0.909 | 0.03 | 0.049 |
| Tier 1 only | 44 | 0.111 | 1.0 | 0.909 | 0.034 | 0.045 |
| Tier 1 + Tier 2 | 44 | 0.111 | 1.0 | 0.909 | 0.042 | 0.063 |

Definitions: hallucination_rate = judge-fail / 36 answerable; refusal_accuracy =
correctly-refused-and-judge-pass / 8 unanswerable; latency = retrieve+generate[+guardrail]
per question; `results/results.json:1` has per-question rows. Rerun with the key set for
LLM numbers (Tier 2 then uses the LLM evaluator; latencies rise). Identical quality
offline is honest: verbatim-quote fallback scores high on Tier 1, so it rarely flags;
Tier 1 cannot catch a verbatim-but-wrong-section quote (q28/q33) — that needs semantic
Tier 2 with an LLM. `tests/test_guardrail.py:1` proves Tier 1 flags true hallucinations
and Tier 2 + logging run on flag.

## 8. Failure log (required)

`failures.md:1` records every wrong output with question, output, failure category, and
root cause, plus counts. Current summary (same 4 failures in each config):

| config | retrieval miss | ungrounded generation | guardrail FP/FN | other |
|---|---:|---:|---:|---:|
| no guardrail | 2 (q28, q33) | 2 (q01/q22/q43 ranking) | 0 | 0 |
| Tier 1 only | 2 | 2 | 0 | 0 |
| Tier 1 + Tier 2 | 2 | 2 | 0 | 0 |

Root causes: home-office queries retrieving `p334-general`/`p587-general` front-matter
instead of `p587-exclusive-regular-use` (needs better section ranking/semantic Tier 2);
terse multi-turn follow-up (q43) with low question-overlap; no guardrail FP/FN this run
(refusals handled correctly).

## 9. Layout

`config.yaml`, `src/{config,llm_client,embeddings,vector_store,ingest,bot,guardrail,eval_judge,run_eval,calibrate}.py`,
`eval/{eval_set.jsonl,calibration_examples.json,baseline.json,prompt_template.txt}`,
`tests/{test_regression,test_guardrail}.py`, `scripts/promptfoo_provider.py`,
`promptfooconfig.yaml`, `results/{results.json,results.md}`, `failures.md`,
`logs/guardrail_decisions.jsonl`, `data/{corpus/*.pdf,chunks.jsonl}`, `requirements.txt`.

## 10. Dependencies (`requirements.txt:1`)

`qdrant-client>=1.9`, `sentence-transformers>=2.2`, `pypdf>=4.0`, `requests>=2.28`,
`pyyaml>=6.0`, `numpy>=1.24`, `scikit-learn>=1.3`, `openai>=1.0`, `pytest>=7.0`,
`tqdm>=4.0`. Python 3.12 venv verified (`pytest`: 4 passed).

## 11. Limitations

- Offline numbers use the extractive fallback + heuristic judge; LLM mode needs the key.
- PDF extraction leaves hyphenation artifacts (partially cleaned in `ingest.chunk_text`);
  `p334-car-truck`/`p334-travel-meals` have only 3/2 chunks, so ranking misses occur.
- Tier 1 is lexical by design (cheap); semantic wrong-section catches require LLM Tier 2.
