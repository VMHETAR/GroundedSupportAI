"""Two-tier response guardrail with decision logging.

Tier 1 (cheap): TF-IDF cosine between response sentences and sliding windows
  over retrieved chunks. Flag if no window clears threshold.
Tier 2 (LLM, only on flag): judges groundedness, coherence, policy compliance.
  Returns pass/fail + rationale. Falls back to heuristic when LLM unavailable.
Must pass both to show; else fallback message offering human handoff.
Logs every decision: tier ran, scores, verdict, latency.
"""
import os, re, json, time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import load_config, llm_settings
from src.llm_client import LLMClient

EVAL_SYSTEM = (
    "You are a strict support-quality evaluator. Given the conversation history, "
    "retrieved excerpts, and the assistant response, judge:\n"
    "(1) groundedness: every factual claim is supported by the excerpts;\n"
    "(2) coherence: the response addresses the user's issue and follows the conversation;\n"
    "(3) policy: no disallowed content, no fabricated rates/forms/deadlines, "
    "refuses cleanly when excerpts lack the answer.\n"
    "Return JSON only: {\"pass\": true/false, \"rationale\": \"...\"}."
)

def sliding_windows(text, window_words=80, stride=40):
    words = re.findall(r"\S+", text)
    if not words:
        return []
    wins = []
    for i in range(0, len(words), stride):
        w = words[i:i + window_words]
        if len(w) < 10 and wins:
            break
        wins.append(" ".join(w))
        if i + window_words >= len(words):
            break
    return wins[:20]

def tier1_score(response, chunks, window_words=80, stride=40):
    """Max TF-IDF cosine between response and any chunk window. Returns (score, best_window)."""
    wins = []
    for c in chunks:
        wins.extend(sliding_windows(c.get("text", ""), window_words, stride))
    if not wins or not response.strip():
        return 0.0, ""
    try:
        vec = TfidfVectorizer(stop_words="english").fit(wins + [response])
        m = vec.transform(wins + [response]).toarray()
        sims = cosine_similarity([m[-1]], m[:-1])[0]
        i = int(sims.argmax())
        return float(sims[i]), wins[i][:200]
    except ValueError:
        # empty vocabulary
        return 0.0, ""

TIER2_HEURISTIC_REFUSAL = re.compile(
    r"(can't verify|cannot verify|not in|don't have enough|no information|human handoff|tax professional)", re.I)

def tier2_heuristic(response, chunks, tier1_score_val):
    # pass refusal-style answers; fail obvious fabrication signals
    if TIER2_HEURISTIC_REFUSAL.search(response):
        return True, "heuristic: clean refusal, nothing to ground"
    if tier1_score_val < 0.10 and len(response) > 400:
        return False, "heuristic: long answer with near-zero lexical overlap"
    return True, "heuristic: lexical overlap sufficient, no policy trigger"

class Guardrail:
    def __init__(self, cfg=None, log_path="logs/guardrail_decisions.jsonl"):
        self.cfg = cfg or load_config()
        g = self.cfg.get("guardrail", {})
        self.threshold = g.get("tier1_threshold", 0.28)
        self.ww = g.get("tier1_window_words", 80)
        self.stride = g.get("tier1_stride_words", 40)
        self.fallback = g.get("fallback_message", "I can't verify this answer; requesting human handoff.")
        s = llm_settings(self.cfg)
        self.evaluator = LLMClient(s["base_url"], s["api_key"], s["evaluator_model"],
                                   s["timeout_s"], 256, 0.0)
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    def check(self, response, chunks, history=""):
        t0 = time.time()
        s1, best = tier1_score(response, chunks, self.ww, self.stride)
        tier1_pass = s1 >= self.threshold
        decision = {"tier1_score": round(s1, 4), "tier1_threshold": self.threshold,
                    "tier1_pass": tier1_pass, "tier1_best_window": best[:200],
                    "tier2_ran": False, "tier2_pass": None, "tier2_rationale": "",
                    "verdict": "pass", "latency_s": 0.0}
        if tier1_pass:
            decision["verdict"] = "pass"
        else:
            # Tier 2 only on flag
            t1 = time.time()
            decision["tier2_ran"] = True
            excerpts = "\n\n".join(f"[{c.get('section','?')}] {c.get('text','')[:1000]}" for c in chunks[:5])
            user_prompt = (f"Conversation:\n{history[-1500:]}\n\nExcerpts:\n{excerpts}\n\n"
                           f"Response:\n{response}\n\nReturn JSON only.")
            llm_text, _, backend = self.evaluator.generate(EVAL_SYSTEM, user_prompt)
            if llm_text.strip():
                try:
                    # extract JSON
                    m = re.search(r"\{.*\}", llm_text, re.S)
                    obj = json.loads(m.group(0)) if m else {}
                    p = obj.get("pass", obj.get("Pass", False))
                    decision["tier2_pass"] = bool(p)
                    decision["tier2_rationale"] = str(obj.get("rationale", llm_text))[:600]
                    decision["tier2_backend"] = "llm"
                except Exception as e:
                    hp, hr = tier2_heuristic(response, chunks, s1)
                    decision["tier2_pass"] = hp
                    decision["tier2_rationale"] = f"llm-parse-failed, {hr}"
                    decision["tier2_backend"] = "heuristic"
            else:
                hp, hr = tier2_heuristic(response, chunks, s1)
                decision["tier2_pass"] = hp
                decision["tier2_rationale"] = hr + " (llm unavailable)"
                decision["tier2_backend"] = "heuristic"
            decision["tier2_latency_s"] = round(time.time() - t1, 3)
            decision["verdict"] = "pass" if decision["tier2_pass"] else "fail"
        decision["latency_s"] = round(time.time() - t0, 3)
        self._log(decision, response, chunks)
        if decision["verdict"] == "pass":
            return response, decision
        return self.fallback, decision

    def _log(self, decision, response, chunks):
        rec = dict(decision)
        rec.update({"response_preview": response[:300],
                    "chunk_sections": [c.get("section", "") for c in chunks[:5]]})
        with open(self.log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
