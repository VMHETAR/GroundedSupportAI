"""RAG support bot: condense -> retrieve -> generate. Generation behind single config."""
import time
from src.config import load_config, llm_settings
from src import embeddings, vector_store
from src.llm_client import LLMClient, extractive_answer

CONDENSE_SYSTEM = "You condense a support conversation into one standalone query. Output only the query."
ANSWER_SYSTEM = (
    "You are a customer-support assistant answering ONLY from the provided IRS guide excerpts. "
    "Rules: (1) Use only the excerpts; do not add outside tax facts, rates, or forms. "
    "(2) If the excerpts do not contain the answer, say you cannot verify it and offer a human handoff. "
    "(3) Cite sources like [p334-car-truck] inline. (4) Be concise and keep language consistent with the question."
)

PROMPT_TEMPLATE = """Condensed issue summary: {condensed}

Conversation history:
{history}

Retrieved excerpts:
{excerpts}

Question: {question}

Answer using only the excerpts above. If the answer is not in the excerpts, refuse and offer a human handoff."""

class RAGBot:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_config()
        s = llm_settings(self.cfg)
        self.gen = LLMClient(s["base_url"], s["api_key"], s["generation_model"],
                             s["timeout_s"], s["max_tokens"], s["temperature"])
        self.cond = LLMClient(s["base_url"], s["api_key"], s["condense_model"],
                              s["timeout_s"], 128, 0.0)
        self.qclient = vector_store.get_client(self.cfg["qdrant"]["path"])
        self.collection = self.cfg["qdrant"]["collection"]
        self.top_n = self.cfg["retrieval"]["top_n"]

    def condense(self, messages):
        """messages: list of {role, content}. Returns standalone query."""
        user_turns = [m["content"] for m in messages if m["role"] == "user"]
        if len(user_turns) <= 1:
            return user_turns[-1] if user_turns else ""
        hist = "\n".join(f"{m['role']}: {m['content']}" for m in messages[-8:])
        text, _, backend = self.cond.generate(
            CONDENSE_SYSTEM,
            f"Condense this conversation into one standalone support query:\n{hist}")
        if text.strip():
            return text.strip()
        # offline fallback: last question + key nouns from history
        return user_turns[-1] + " (context: " + " ".join(user_turns[:-1])[-200:] + ")"

    def retrieve(self, query):
        qv = embeddings.embed([query])[0]
        return vector_store.search(self.qclient, self.collection, qv, self.top_n)

    def answer(self, messages):
        t0 = time.time()
        question = messages[-1]["content"] if messages else ""
        condensed = self.condense(messages)
        chunks = self.retrieve(condensed)
        history = "\n".join(f"{m['role']}: {m['content']}" for m in messages[-6:])
        excerpts = "\n\n".join(f"[{c.get('section', c.get('source','?'))}] {c['text'][:1200]}" for c in chunks)
        prompt = PROMPT_TEMPLATE.format(condensed=condensed, history=history,
                                        excerpts=excerpts, question=question)
        text, gen_lat, backend = self.gen.generate(ANSWER_SYSTEM, prompt)
        if not text.strip():
            text = extractive_answer(question, chunks)
            backend = "extractive-fallback"
        total = time.time() - t0
        return {"response": text, "chunks": chunks, "condensed": condensed,
                "latency_s": total, "gen_latency_s": gen_lat, "backend": backend}
