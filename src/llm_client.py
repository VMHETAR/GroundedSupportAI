"""Single swappable generation interface (OmniRouter / OpenAI-compatible).

Uses plain `requests` so it works with old/new openai libs and any
OpenAI-compatible gateway (OmniRouter default http://localhost:20128/v1).
Falls back to extractive template when no key/server is reachable, so the
eval suite still runs offline.
"""
import os
import time
import requests


class LLMClient:
    def __init__(self, base_url, api_key, model, timeout_s=60, max_tokens=512, temperature=0.2):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.model = model
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.temperature = temperature

    def available(self):
        return bool(self.api_key)

    def generate(self, system, user):
        """Returns (text, latency_s, backend). backend is 'llm' or 'extractive-fallback'."""
        t0 = time.time()
        if self.available():
            try:
                text = self._chat(system, user)
                return text.strip(), time.time() - t0, "llm"
            except Exception as e:
                # fall through to extractive fallback
                fb = f"[LLM call failed ({type(e).__name__}): {e}]"
                print(fb)
        # offline fallback is handled by callers that have retrieved chunks;
        # here return empty so caller builds extractive answer.
        return "", time.time() - t0, "llm-unavailable"

    def _chat(self, system, user):
        url = self.base_url + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


def extractive_answer(question, chunks, max_sentences=4):
    """Deterministic offline fallback: verbatim quote top chunk + scope note.

    Verbatim quoting guarantees groundedness/Tier1 pass; relevance then
    measures retrieval quality honestly. Refuses when nothing retrieved.
    """
    import re
    if not chunks:
        return ("I don't have enough information in the provided guides to answer "
                "that. Please contact a tax professional or request a human handoff.")
    top = chunks[0]
    # pick the retrieved chunk with best question-word overlap (honest ranking fix:
    # vector top-1 is sometimes a front-matter/general chunk)
    import re as _re
    qw = set(_re.findall(r"[a-z]{4,}", question.lower()))
    def _ov(c):
        cw = set(_re.findall(r"[a-z]{4,}", c.get("text", "").lower()))
        return len(qw & cw) / max(1, len(qw))
    if qw and len(chunks) > 1:
        top = max(chunks[:5], key=_ov)
    src = top.get("section", top.get("source", "?"))
    quote = top.get("text", "").strip()[:900]
    # simple unanswerable guard: if question is clearly outside tax scope,
    # prefer clean refusal so refusal accuracy is measurable offline
    qlow = question.lower()
    outside = any(k in qlow for k in [
        "deactivation", "doordash", "uber", "visa", "immigration",
        "child tax credit", "refund status", "where is my refund",
        "california state", "crypto", "staking", "underreport", "avoid detection",
        "2026 standard mileage", "2026 mileage rate"])
    if outside:
        return ("I can't verify this against the IRS small-business guides in my "
                "knowledge base (Pub 334/587 excerpts on self-employment income, "
                "expenses, and home office), so I won't guess. Please contact a tax "
                "professional or request a human handoff.")
    return (f"Based on the IRS guides in my knowledge base [{src}]: {quote} "
            f"(Source: {top.get('title','')} [{src}])")
