"""Context Builder for Kuryecini Ops Co-Pilot"""
import os
import json
from typing import Dict, Any

MASK_KEYS = {"MONGODB_URI", "MONGO_URL", "SENTRY_DSN", "OPENAI_KEY", "OPENAI_API_KEY", "LLM_API_KEY", "EMERGENT_LLM_KEY"}


def mask_env(v: str) -> str:
    """Mask sensitive environment variable"""
    if not v:
        return v
    return "***"


def build_context(panel: str) -> Dict[str, Any]:
    """
    Build panel-aware context with masked sensitive data
    
    Args:
        panel: One of müşteri|işletme|kurye|admin|multi
        
    Returns:
        Context dict with env, services, version, routes
    """
    env = {
        "NODE_ENV": os.getenv("NODE_ENV"),
        "API_BASE_URL": os.getenv("API_BASE_URL"),
        "MONGODB_URI": mask_env(os.getenv("MONGODB_URI") or os.getenv("MONGO_URL")),
        "SENTRY_DSN": mask_env(os.getenv("SENTRY_DSN")),
        "OPENAI_KEY": mask_env(os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("EMERGENT_LLM_KEY")),
    }
    return {
        "panel": panel or "müşteri",
        "env": env,
        "services": {"api": "unknown", "db": "unknown", "maps": "unknown", "auth": "unknown"},
        "version": {"git_sha": os.getenv("GIT_SHA", "unknown"), "branch": os.getenv("BRANCH", "unknown")},
        "routes": ["/health", "/restaurants", "/addresses", "/orders", "/businesses", "/couriers"],
    }


def inject_context(system_prompt: str, panel: str, ctx: Dict[str, Any]) -> str:
    """
    Inject context into system prompt
    
    Args:
        system_prompt: Base system prompt
        panel: Panel name
        ctx: Context dict from build_context()
        
    Returns:
        System prompt with injected context
    """
    masked_json = json.dumps(ctx, ensure_ascii=False, indent=2)
    return f"{system_prompt}\n\n[Konuşma Bağlamı]\nPanel: {panel}\nContext(JSON): {masked_json}"