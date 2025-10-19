"""
AI Provider Abstraction Layer
Supports both Emergent LLM Key (via emergentintegrations) and OpenAI Async SDK
Automatic fallback between providers on error
"""

import os
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager
import asyncio

# Configuration from environment
DEFAULT_PROVIDER = os.getenv("AI_PROVIDER", "emergent")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
FF_OPENAI = os.getenv("FEATURE_OPENAI_PROVIDER", "true").lower() == "true"


@asynccontextmanager
async def _openai_client():
    """Create OpenAI AsyncClient with optional custom key/base"""
    from openai import AsyncOpenAI
    
    key = os.getenv("LLM_API_KEY") or os.getenv("EMERGENT_LLM_KEY") or None
    base = os.getenv("LLM_API_BASE") or None
    
    if not key:
        raise RuntimeError("OpenAI provider requires LLM_API_KEY or EMERGENT_LLM_KEY")
    
    client = AsyncOpenAI(api_key=key, base_url=base)
    try:
        yield client
    finally:
        await client.close()


async def _stream_openai(system: str, user: str, model: str) -> AsyncIterator[str]:
    """Stream chat using OpenAI Async SDK"""
    async with _openai_client() as client:
        response = await client.chat.completions.create(
            model=model,
            temperature=0.4,
            max_tokens=900,
            top_p=1.0,
            stream=True,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


async def _stream_emergent(system: str, user: str, model: str) -> AsyncIterator[str]:
    """Stream chat using emergentintegrations (existing implementation)"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise RuntimeError("Emergent provider requires EMERGENT_LLM_KEY")
        
        # Create chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id=f"ai_assistant_{asyncio.current_task().get_name()}",
            system_message=system
        ).with_model("openai", model)
        
        # Send message and get response
        user_message = UserMessage(text=user)
        response = await chat.send_message(user_message)
        
        # Simulate streaming by chunking the response
        chunk_size = 30
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i+chunk_size]
            yield chunk
            await asyncio.sleep(0.03)  # Smooth streaming effect
            
    except Exception as e:
        raise RuntimeError(f"Emergent streaming failed: {str(e)}")


async def stream_chat(
    system: str,
    user: str,
    model: Optional[str] = None,
    prefer: Optional[str] = None
) -> AsyncIterator[str]:
    """
    Stream chat completion with automatic provider fallback
    
    Args:
        system: System prompt
        user: User message
        model: Model name (default: from env)
        prefer: Preferred provider ("emergent" | "openai" | None)
        
    Yields:
        Text chunks from LLM
        
    Fallback logic:
        - Try preferred provider first
        - On error, try alternative provider once
        - If both fail, raise exception
    """
    model = model or DEFAULT_MODEL
    provider = prefer or DEFAULT_PROVIDER
    tried_alt = False
    
    # Validate OpenAI provider availability
    if provider == "openai" and not FF_OPENAI:
        print(f"⚠️ OpenAI provider disabled by feature flag, falling back to Emergent")
        provider = "emergent"
    
    async def use_provider(provider_name: str) -> AsyncIterator[str]:
        """Execute streaming with specified provider"""
        if provider_name == "openai":
            if not FF_OPENAI:
                raise RuntimeError("OpenAI provider disabled by feature flag")
            async for delta in _stream_openai(system, user, model):
                yield delta
        else:  # emergent
            async for delta in _stream_emergent(system, user, model):
                yield delta
    
    # Main streaming loop with fallback
    while True:
        try:
            print(f"🔄 Attempting streaming with provider: {provider}")
            async for delta in use_provider(provider):
                yield delta
            print(f"✅ Streaming completed with provider: {provider}")
            break
            
        except Exception as e:
            print(f"❌ Provider {provider} failed: {str(e)}")
            
            if tried_alt:
                # Both providers failed
                raise RuntimeError(
                    f"Her iki sağlayıcı da başarısız oldu. Lütfen AI ayarlarını kontrol edin."
                )
            
            # Try alternative provider
            alt_provider = "emergent" if provider == "openai" else "openai"
            print(f"🔄 Falling back to {alt_provider}")
            provider = alt_provider
            tried_alt = True


def current_provider_meta() -> dict:
    """Get current provider metadata for display"""
    provider = os.getenv("AI_PROVIDER", "emergent")
    
    # Check if OpenAI is actually available
    if provider == "openai" and not FF_OPENAI:
        provider = "emergent"
    
    return {
        "provider": provider,
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "openai_available": FF_OPENAI
    }


def get_provider_status() -> dict:
    """Get detailed provider status for health checks"""
    emergent_key = bool(os.getenv("EMERGENT_LLM_KEY"))
    openai_key = bool(os.getenv("LLM_API_KEY"))
    
    return {
        "emergent": {
            "available": emergent_key,
            "key_configured": emergent_key
        },
        "openai": {
            "available": FF_OPENAI and (openai_key or emergent_key),
            "key_configured": openai_key or emergent_key,
            "feature_flag": FF_OPENAI
        },
        "current": DEFAULT_PROVIDER
    }
