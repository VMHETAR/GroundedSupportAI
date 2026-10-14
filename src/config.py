"""Load config.yaml (single swappable config)."""
import os
import yaml

_CONFIG_CACHE = None

def load_config(path="config.yaml"):
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    # resolve relative to repo root (cwd or file location)
    candidates = [path, os.path.join(os.path.dirname(__file__), "..", path)]
    for c in candidates:
        if os.path.exists(c):
            with open(c) as f:
                _CONFIG_CACHE = yaml.safe_load(f)
                return _CONFIG_CACHE
    raise FileNotFoundError(f"config.yaml not found (tried {candidates})")

def llm_settings(cfg):
    llm = cfg.get("llm", {})
    api_key = os.environ.get(llm.get("api_key_env", "OMNIROUTER_API_KEY"), "") or \
              os.environ.get("OPENAI_API_KEY", "") or \
              os.environ.get("OMNIROUTER_API_KEY", "")
    base_url = os.environ.get(llm.get("base_url_env", "OMNIROUTER_BASE_URL"), "") or \
               os.environ.get("OPENAI_BASE_URL", "") or \
               llm.get("default_base_url", "http://localhost:20128/v1")
    return {
        "provider": llm.get("provider", "omnirouter"),
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),
        "generation_model": llm.get("generation_model", "llama3.1:8b"),
        "condense_model": llm.get("condense_model", "llama3.1:8b"),
        "evaluator_model": llm.get("evaluator_model", "llama3.1:8b"),
        "judge_model": llm.get("judge_model", "llama3.1:8b"),
        "timeout_s": llm.get("timeout_s", 60),
        "max_tokens": llm.get("max_tokens", 512),
        "temperature": llm.get("temperature", 0.2),
    }
