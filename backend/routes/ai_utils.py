"""AI Utilities and Tool Stubs for Kuryecini Ops Co-Pilot"""
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

# File paths
BASE_DIR = Path(__file__).parent.parent
TOOLS_FILE = BASE_DIR / "ops" / "tools.schema.json"
PROMPT_FILE = BASE_DIR / "ops" / "system_prompt.md"
FEWSHOTS_FILE = BASE_DIR / "ops" / "fewshots.md"


def load_system_prompt() -> str:
    """Load system prompt with few-shots"""
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        base = f.read()
    few = ""
    if FEWSHOTS_FILE.exists():
        with open(FEWSHOTS_FILE, "r", encoding="utf-8") as f:
            few = f"\n\n[Örnekler]\n{f.read()}"
    return base + few


def build_and_inject_context(system_prompt: str, panel: str) -> str:
    """Build context and inject into system prompt"""
    from ai.context_builder import build_context, inject_context
    
    ctx = build_context(panel)
    return inject_context(system_prompt, panel, ctx)


def ask_llm(system_prompt_with_ctx: str, user_message: str, model: Optional[str] = None) -> str:
    """Ask LLM with context"""
    from ai.ai_provider_copilot import chat
    
    return chat(system_prompt_with_ctx, user_message, model)


# ==================== TOOL STUBS ====================
# These are basic implementations - can be enhanced later


def tool_http_get(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """HTTP GET tool stub"""
    try:
        import httpx
        with httpx.Client(timeout=10.0, verify=True) as c:
            r = c.get(url, headers=headers or {})
            return {"status": r.status_code, "text": r.text[:4000]}
    except Exception as e:
        return {"error": str(e)}


def tool_logs_tail(path: str = "./logs/app.log", limit: int = 200) -> Dict[str, Any]:
    """Log tail tool stub"""
    try:
        if not os.path.exists(path):
            # Try supervisor logs
            path = "/var/log/supervisor/backend.out.log"
        if not os.path.exists(path):
            return {"error": f"log not found: {path}"}
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-limit:]
        return {"lines": lines}
    except Exception as e:
        return {"error": str(e)}


def tool_db_query(collection: str, action: str, filter_: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """MongoDB query tool stub (requires async in real usage)"""
    # This is a sync stub - should be converted to async for production
    from pymongo import MongoClient
    uri = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    if not uri:
        return {"error": "MONGO_URL missing"}
    try:
        client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=3000)
        db_name = os.getenv("DB_NAME", "kuryecini")
        db = client[db_name]
        col = db[collection]
        if action == "count":
            return {"count": col.count_documents(filter_ or {})}
        if action == "find_one":
            doc = col.find_one(filter_ or {}, projection={"_id": 0})
            return {"doc": doc}
        if action == "list_indexes":
            return {"indexes": [ix for ix in col.list_indexes()]}
        return {"error": f"unknown action {action}"}
    except Exception as e:
        return {"error": str(e)}


def tool_env_list(mask: bool = True) -> Dict[str, Any]:
    """Environment variables tool stub"""
    keys = ["NODE_ENV", "API_BASE_URL", "MONGO_URL", "MONGODB_URI", "SENTRY_DSN", "OPENAI_API_KEY", "LLM_API_KEY", "EMERGENT_LLM_KEY"]
    out = {}
    for k in keys:
        v = os.getenv(k)
        out[k] = "***" if (mask and v) else v
    return out