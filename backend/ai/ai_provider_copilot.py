"""AI Provider for Kuryecini Ops Co-Pilot (OpenAI + Emergent)"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

# Check which API key is available and initialize appropriate client
emergent_key = os.getenv("EMERGENT_LLM_KEY")
openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

if emergent_key:
    # Use Emergent LLM integration
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = emergent_key
    use_emergent = True
    print(f"🤖 Using Emergent LLM API with key: {api_key[:15]}...")
elif openai_key:
    # Use OpenAI directly
    from openai import OpenAI
    api_key = openai_key
    use_emergent = False
    client = OpenAI(api_key=api_key)
    print(f"🤖 Using OpenAI API with key: {api_key[:15]}...")
else:
    raise RuntimeError("No API key found. Set OPENAI_API_KEY, LLM_API_KEY, or EMERGENT_LLM_KEY")

RESPONSE_PREFIX = (
    "Aşağıdaki ZORUNLU formatta cevapla:\n"
    "Hızlı Teşhis → Derin RCA → Kontrol Komutları → Patch → Test → İzleme & Alarm → DoD.\n"
)


def today_istanbul() -> str:
    """Get today's date in Europe/Istanbul timezone"""
    return datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d")


def chat(system_prompt: str, user_message: str, model: Optional[str] = None) -> str:
    """
    Send chat completion request to OpenAI or Emergent LLM
    
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
    
    user_content = RESPONSE_PREFIX + f"Kullanıcı Sorusu: {user_message}"
    
    if use_emergent:
        # Use Emergent LLM integration
        try:
            chat_session = LlmChat(
                api_key=api_key,
                session_id=f"copilot_{hash(user_message) % 10000}",
                system_message=system_prompt
            ).with_model("openai", model)
            
            user_msg = UserMessage(text=user_content)
            response = chat_session.send_message(user_msg)
            return response
        except Exception as e:
            print(f"❌ Emergent LLM Error: {e}")
            raise e
    else:
        # Use OpenAI directly
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return resp.choices[0].message.content or ""