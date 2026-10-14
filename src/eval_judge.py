"""LLM judge with rubric: retrieval correctness, groundedness, relevance, language consistency.

Returns 1-5 per dimension + overall pass/fail. Heuristic fallback when LLM
unavailable so eval runs offline. Calibrate via eval/calibration_examples.json.
"""
import re, json
from src.config import load_config, llm_settings
from src.llm_client import LLMClient

JUDGE_SYSTEM = (
    "You are an eval judge for a tax-support RAG bot grounded in IRS Pub 334/587 excerpts. "
    "Score 1-5 on: retrieval_correctness (do retrieved sections match expected_source?), "
    "groundedness (claims supported by excerpts?), relevance (answers the question?), "
    "language_consistency (same language as question, no mixed-language drift?). "
    "Return JSON only: {\"retrieval\": n, \"groundedness\": n, \"relevance\": n, "
    "\"language\": n, \"pass\": true/false, \"rationale\": \"...\"}. "
    "Pass requires groundedness>=4 and relevance>=4; unanswerable questions pass only if the "
    "response refuses and offers handoff."
)

REFUSAL_RE = re.compile(r"(can't verify|cannot verify|not in my knowledge|don't have enough|no information in the provided|human handoff|tax professional)", re.I)

def judge(question, response, retrieved_sections, expected_source, answerable,
          history="", llm=None):
    excerpts_note = f"retrieved={retrieved_sections} expected={expected_source} answerable={answerable}"
    prompt = (f"Question: {question}\nResponse: {response}\n{excerpts_note}\n"
              f"History: {history[-500:]}\nReturn JSON only.")
    if llm is None:
        cfg = load_config()
        s = llm_settings(cfg)
        llm = LLMClient(s["base_url"], s["api_key"], s["judge_model"], s["timeout_s"], 256, 0.0)
    text, _, backend = llm.generate(JUDGE_SYSTEM, prompt)
    if text.strip():
        try:
            m = re.search(r"\{.*\}", text, re.S)
            obj = json.loads(m.group(0))
            return {"retrieval": int(obj.get("retrieval", 3)),
                    "groundedness": int(obj.get("groundedness", 3)),
                    "relevance": int(obj.get("relevance", 3)),
                    "language": int(obj.get("language", 5)),
                    "pass": bool(obj.get("pass", False)),
                    "rationale": str(obj.get("rationale", ""))[:500],
                    "backend": "llm"}
        except Exception:
            pass
    # heuristic fallback (offline)
    is_refusal = bool(REFUSAL_RE.search(response))
    if isinstance(expected_source, str):
        expected_source = [expected_source]
    hit = any(e in (retrieved_sections or []) for e in (expected_source or [])) if expected_source else True
    if not answerable:
        passed = is_refusal
        return {"retrieval": 5 if passed else 2, "groundedness": 5 if passed else 2,
                "relevance": 5 if passed else 2, "language": 5,
                "pass": passed, "rationale": "heuristic: unanswerable -> refusal required",
                "backend": "heuristic"}
    # answerable: retrieval hit + non-refusal + overlap with question
    qw = set(re.findall(r"[a-z]{4,}", question.lower()))
    rw = set(re.findall(r"[a-z]{4,}", response.lower()))
    overlap = len(qw & rw) / max(1, len(qw))
    grounded = 4 if (hit and not is_refusal) else (2 if is_refusal else 3)
    rel = 4 if overlap >= 0.2 and not is_refusal else 2
    passed = hit and grounded >= 4 and rel >= 4
    return {"retrieval": 5 if hit else 2, "groundedness": grounded, "relevance": rel,
            "language": 5, "pass": passed,
            "rationale": f"heuristic: hit={hit} overlap={overlap:.2f} refusal={is_refusal}",
            "backend": "heuristic"}
