"""AI Provider for Kuryecini Ops Co-Pilot (OpenAI + Emergent)"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from typing import Optional

# Initialize OpenAI client (will use EMERGENT_LLM_KEY or custom key)
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("EMERGENT_LLM_KEY")
if not api_key:
    raise RuntimeError("No API key found. Set OPENAI_API_KEY, LLM_API_KEY, or EMERGENT_LLM_KEY")

client = OpenAI(api_key=api_key)

RESPONSE_PREFIX = (
    "Aşağıdaki ZORUNLU formatta cevapla:\n"
    "Hızlı Teşhis → Derin RCA → Kontrol Komutları → Patch → Test → İzleme & Alarm → DoD.\n"
)


def today_istanbul() -> str:
    """Get today's date in Europe/Istanbul timezone"""
    return datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d")


def chat(system_prompt: str, user_message: str, model: Optional[str] = None) -> str:
    """
    Send chat completion request to OpenAI (or Emergent LLM Key)
    
    Args:
        system_prompt: System prompt with context
        user_message: User question
        model: Model name (default: gpt-4o-mini)
        
    Returns:
        LLM response text
    """
    # Replace {{TODAY}} placeholder
    system_prompt = system_prompt.replace("{{TODAY}}", today_istanbul())
    
    # Default model
    if not model:
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": RESPONSE_PREFIX + f"Kullanıcı Sorusu: {user_message}"},
        ],
    )
    return resp.choices[0].message.content or ""