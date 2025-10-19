"""
Panel AI Assistant Backend Endpoint - HARDENED
Streaming Turkish AI responses with proper PII redaction and panel isolation
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime, timezone, timedelta
import os
import asyncio
import re
import json
from dotenv import load_dotenv

load_dotenv()

# Import auth
from auth_dependencies import get_admin_user

router = APIRouter(prefix="/admin/ai", tags=["AI Assistant"])
db_client: Optional[AsyncIOMotorClient] = None


def set_db_client(client: AsyncIOMotorClient):
    """Set database client from main server"""
    global db_client
    router.db_client = client


def get_db():
    """Get database instance"""
    if not hasattr(router, 'db_client') or router.db_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not initialized"
        )
    return router.db_client.kuryecini


class AIAskRequest(BaseModel):
    """AI Assistant query request"""
    question: str = Field(..., min_length=1, max_length=2000, description="User question in Turkish")
    scope: Literal["customer", "business", "courier", "multi"] = Field(default="business", description="Panel scope")
    time_window_minutes: int = Field(default=60, ge=1, le=1440, description="Time window in minutes")
    include_logs: bool = Field(default=True, description="Include log summaries")
    mode: Literal["metrics", "summary", "patch"] = Field(default="summary", description="Response mode")


def redact_pii(text: str) -> str:
    """
    Redact PII while preserving sentence structure
    Uses placeholders instead of removal to maintain readability
    """
    if not text:
        return text
    
    # Email: user@domain.com -> <MASK:EMAIL>
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '<MASK:EMAIL>', text)
    
    # Turkish phone: +90 5XX XXX XX XX, 0 5XX XXX XX XX
    text = re.sub(r'(\+90|0)?[\s\-]?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', '<MASK:PHONE>', text)
    
    # IBAN: TR XX XXXX ...
    text = re.sub(r'\bTR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b', '<MASK:IBAN>', text, flags=re.IGNORECASE)
    
    # JWT/Bearer tokens (long alphanumeric strings)
    text = re.sub(r'\b(eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})\b', '<MASK:TOKEN>', text)
    text = re.sub(r'\bBearer\s+[A-Za-z0-9_-]{30,}\b', '<MASK:TOKEN>', text, flags=re.IGNORECASE)
    
    # Card numbers: XXXX XXXX XXXX XXXX
    text = re.sub(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '<MASK:CARD>', text)
    
    # Precise addresses (street numbers + street names)
    text = re.sub(r'\b\d{1,5}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+(Sokak|Cadde|Bulvarı|Sk\.|Cd\.)', '<MASK:ADDR>', text, flags=re.IGNORECASE)
    
    return text


def trim_log_sample(log_text: str, max_bytes: int = 2000) -> str:
    """
    Trim log sample to max bytes while preserving UTF-8 boundaries
    """
    if not log_text:
        return log_text
    
    encoded = log_text.encode('utf-8')
    if len(encoded) <= max_bytes:
        return log_text
    
    # Trim to max_bytes and decode, ignoring incomplete characters
    trimmed = encoded[:max_bytes].decode('utf-8', errors='ignore')
    return trimmed + "..."


def get_turkish_system_prompt(scope: str, mode: str) -> str:
    """
    Get Turkish system prompt based on panel scope and mode
    """
    base_prompt = (
        "Sen Kuryecini'nin panel-bilinçli sistem asistanısın. "
        "YALNIZCA seçilen panel verilerini kullan. "
        "PII maskelerini (<MASK:EMAIL>, <MASK:PHONE>, vb.) asla açma, korunmalı. "
        "Kısa, uygulanabilir, Türkçe yanıt ver."
    )
    
    # Mode-specific instructions
    mode_instructions = {
        "metrics": "Metrik yorumlamaya odaklan. Sayısal değerleri analiz et ve trend yorumu yap.",
        "summary": "Log ve cluster özetleri ile birlikte Kök Neden Analizi (RCA) yap.",
        "patch": "RCA ile birlikte kısa kod yaması (FastAPI/React/MongoDB) ve test önerisi ver."
    }
    
    # Scope-specific focus
    scope_focus = {
        "customer": "Müşteri paneli: Restoran keşfi, sepet/checkout, kupon, sipariş takibi.",
        "business": "İşletme paneli: Sipariş liste/onay, menü yönetimi, çalışma saatleri, SLA.",
        "courier": "Kurye paneli: Görev kabul, WS bağlantısı, rota/konum, ETA.",
        "multi": "Üç paneli ayrı ayrı özetle, etkileşimleri açıkla, çapraz etkileri analiz et."
    }
    
    # Response format
    format_template = """
Yanıt formatı:
**[Başlık]**
**Bulgular** (son X dakikada)
- Bulgu 1
- Bulgu 2

**Kök Nedenler**
- Neden 1
- Neden 2

**Hızlı Çözümler**
- Anında: ...
- Konfigürasyon: ...
"""
    
    if mode == "patch":
        format_template += """
**Kod Örneği**
```python
# Örnek düzeltme
```

**İzleme/Test**
- Metrik: ...
- Test: ...
"""
    
    full_prompt = f"{base_prompt}\n\n{mode_instructions.get(mode, '')}\n\n{scope_focus.get(scope, '')}\n\n{format_template}"
    
    return full_prompt


async def build_panel_context(scope: str, time_window_minutes: int, include_logs: bool, db) -> dict:
    """
    Build panel-aware context with proper isolation and redaction
    """
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(minutes=time_window_minutes)
    
    # Initialize context structure with Turkish field names
    context = {
        "baglam": {
            "panel": scope,
            "zaman_dilimi_dk": time_window_minutes,
            "metrikler": {},
            "kume_ozetleri": [],
            "ornek_loglar": []
        }
    }
    
    # Fetch metrics (mock for now, can be enhanced with real system metrics)
    if scope == "multi":
        # Multi-panel: fetch all three
        context["baglam"]["metrikler"] = {
            "customer": {"p50": "110ms", "p95": "420ms", "hata_orani": "1.8%", "ws": 12},
            "business": {"p50": "95ms", "p95": "380ms", "hata_orani": "2.1%", "ws": 23},
            "courier": {"p50": "130ms", "p95": "450ms", "hata_orani": "1.5%", "ws": 8}
        }
    else:
        # Single panel metrics
        context["baglam"]["metrikler"] = {
            "p50": "105ms",
            "p95": "395ms",
            "hata_orani": "1.9%",
            "kuyruk": 4,
            "aktif_ws": 15 if scope == "business" else (8 if scope == "customer" else 5),
            "siparis_dak": "8/dk" if scope in ["customer", "business"] else "N/A"
        }
    
    # Fetch log samples if requested
    if include_logs:
        try:
            # Query ai_logs collection filtered by app field
            app_filter = scope if scope != "multi" else {"$in": ["customer", "business", "courier"]}
            
            logs_cursor = db.ai_logs.find(
                {
                    "app": app_filter,
                    "timestamp": {"$gte": start_time}
                },
                {"message": 1, "level": 1, "timestamp": 1, "_id": 0}
            ).sort("timestamp", -1).limit(10)
            
            logs = await logs_cursor.to_list(length=10)
            
            if logs:
                # Redact and trim log samples
                context["baglam"]["ornek_loglar"] = [
                    trim_log_sample(redact_pii(log.get("message", "")))
                    for log in logs
                ]
            else:
                context["baglam"]["ornek_loglar"] = [
                    "Son {} dakikada log kaydı bulunamadı.".format(time_window_minutes)
                ]
            
            # Fetch error clusters
            clusters_cursor = db.ai_clusters.find(
                {
                    "app": app_filter,
                    "last_seen": {"$gte": start_time}
                },
                {"fingerprint": 1, "sample_message": 1, "count_24h": 1, "_id": 0}
            ).sort("count_24h", -1).limit(5)
            
            clusters = await clusters_cursor.to_list(length=5)
            
            if clusters:
                context["baglam"]["kume_ozetleri"] = [
                    {
                        "baslik": cluster.get("fingerprint", "Unknown")[:50],
                        "ornek": trim_log_sample(redact_pii(cluster.get("sample_message", "")), 500),
                        "siklik_24s": cluster.get("count_24h", 0)
                    }
                    for cluster in clusters
                ]
        except Exception as e:
            print(f"⚠️ Log fetch error: {str(e)}")
            context["baglam"]["ornek_loglar"] = ["Log verisi alınamadı."]
    
    return context


async def stream_ai_response(question: str, scope: str, context: dict, mode: str, settings: dict):
    """
    Stream AI response using emergentintegrations
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Determine API key
        api_key = None
        if settings and settings.get("openai_api_key") and not settings.get("use_emergent_key", True):
            api_key = settings["openai_api_key"]
        else:
            api_key = os.environ.get("EMERGENT_LLM_KEY")
        
        if not api_key:
            yield "data: " + '{"error": "API key not configured"}\n\n'
            return
        
        # Get system prompt
        system_prompt = get_turkish_system_prompt(scope)
        answer_format = get_turkish_answer_format()
        
        # Build user message with context
        context_str = f"""
Panel: {scope}
Zaman Aralığı: {context.get('time_window_minutes')} dakika
Metrikler: {context.get('metrics')}
"""
        
        if context.get('logs_included'):
            context_str += f"\nLog Özeti: {context.get('log_summary')}\nÖnemli Hatalar: {context.get('top_errors')}"
        
        user_message_text = f"{context_str}\n\nSoru: {question}\n\n{answer_format}"
        
        # Create chat instance
        model = settings.get("default_model", "gpt-4o-mini") if settings else "gpt-4o-mini"
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"panel_ai_{datetime.now().timestamp()}",
            system_message=system_prompt
        ).with_model("openai", model)
        
        # Send message and stream response
        user_message = UserMessage(text=user_message_text)
        
        # For now, send full response (streaming not yet implemented in simple way)
        response = await chat.send_message(user_message)
        
        # Stream response in chunks
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i+chunk_size]
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.05)  # Simulate streaming delay
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_msg = f"AI sorgu hatası: {str(e)}"
        yield f"data: {error_msg}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/ask", summary="Panel-Aware AI Assistant Query")
async def ai_ask(
    request: AIAskRequest,
    current_user: dict = Depends(get_admin_user)
):
    """
    Panel-aware AI assistant query with streaming response
    
    **RBAC**: SuperAdmin & Operasyon only
    
    **Scope options**:
    - customer: Customer panel context (restaurant discovery, orders, cart)
    - business: Business panel context (order management, menu, KYC)
    - courier: Courier panel context (task acceptance, routing, location)
    - multi: Cross-panel analysis
    
    **Mode options**:
    - metrics: Focus on metrics analysis
    - summary: General summary with RCA
    - patch: Include code examples and fixes
    
    Returns streaming response in SSE format.
    """
    db = get_db()
    
    # Get AI settings
    settings_doc = await db.admin_settings_ai.find_one({"id": "ai_settings_default"})
    settings = settings_doc if settings_doc else {}
    
    # Rate limiting check (simplified - in production use Redis)
    # For now, just log the request
    print(f"📊 AI Query: user={current_user.get('email')}, scope={request.scope}, mode={request.mode}")
    
    # Build context
    context = await build_panel_context(
        request.scope,
        request.time_window_minutes,
        request.include_logs,
        db
    )
    
    # Audit log
    await db.ai_audit_logs.insert_one({
        "user_id": current_user.get("id", current_user.get("_id")),
        "user_email": current_user.get("email"),
        "question": request.question[:200],  # Truncate
        "scope": request.scope,
        "mode": request.mode,
        "time_window_minutes": request.time_window_minutes,
        "timestamp": datetime.now(timezone.utc)
    })
    
    # Return streaming response
    return StreamingResponse(
        stream_ai_response(request.question, request.scope, context, request.mode, settings),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
