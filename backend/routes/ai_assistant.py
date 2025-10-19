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
    provider: Optional[Literal["emergent", "openai"]] = Field(None, description="Preferred AI provider")


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


async def stream_ai_response(question: str, scope: str, context: dict, mode: str, settings: dict, prefer_provider: Optional[str] = None):
    """
    Stream REAL AI response using provider abstraction - Dual OpenAI/Emergent support
    """
    # Import provider abstraction
    from ai_provider import stream_chat, current_provider_meta
    
    # Telemetry data
    telemetry = {
        "provider": prefer_provider or current_provider_meta()["provider"],
        "model": settings.get("default_model", "gpt-4o-mini") if settings else "gpt-4o-mini",
        "scope": scope,
        "mode": mode,
        "time_window": context.get("baglam", {}).get("zaman_dilimi_dk", 60)
    }
    
    try:
        # Log telemetry (no PII)
        print(f"📊 LLM Call: provider={telemetry['provider']}, model={telemetry['model']}, scope={scope}, mode={mode}, window={telemetry['time_window']}dk")
        
        # Get system prompt
        system_prompt = get_turkish_system_prompt(scope, mode)
        
        # Build user message with context (Turkish fields)
        context_data = context.get("baglam", {})
        context_str = f"""
Panel: {context_data.get('panel')}
Zaman Dilimi: {context_data.get('zaman_dilimi_dk')} dakika

Metrikler:
{json.dumps(context_data.get('metrikler', {}), ensure_ascii=False, indent=2)}
"""
        
        if context_data.get('kume_ozetleri'):
            context_str += f"\n\nHata Kümeleri:\n"
            for cluster in context_data.get('kume_ozetleri', [])[:3]:
                context_str += f"- {cluster.get('baslik')} (24s'de {cluster.get('siklik_24s')} kez)\n  Örnek: {cluster.get('ornek')[:200]}\n"
        
        if context_data.get('ornek_loglar'):
            context_str += f"\n\nÖrnek Loglar:\n"
            for log in context_data.get('ornek_loglar', [])[:5]:
                context_str += f"- {log[:300]}\n"
        
        user_message_text = f"{context_str}\n\nSoru: {question}"
        
        # Send metadata first
        meta_payload = json.dumps({
            "meta": {
                "provider": telemetry["provider"],
                "model": telemetry["model"],
                "scope": scope,
                "mode": mode
            }
        }, ensure_ascii=False)
        yield f"data: {meta_payload}\n\n"
        
        # Stream using provider abstraction with automatic fallback
        try:
            async for delta in stream_chat(
                system=system_prompt,
                user=user_message_text,
                model=telemetry["model"],
                prefer=prefer_provider
            ):
                chunk_json = json.dumps({"delta": delta}, ensure_ascii=False)
                yield f"data: {chunk_json}\n\n"
            
            yield "data: [DONE]\n\n"
            
            # Log success
            print(f"✅ LLM Success: provider={telemetry['provider']}, model={telemetry['model']}")
            return
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ LLM Error: {error_msg}")
            
            # All retries exhausted - fail with error
            error_payload = json.dumps({
                "error": "Model yanıtı alınamadı. Lütfen ayarları kontrol edip tekrar deneyin.",
                "llm_call_failed": True
            }, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"
            yield "data: [DONE]\n\n"
            return
        
    except Exception as e:
        error_msg = f"LLM sistem hatası: {str(e)}"
        print(f"❌ LLM System Error: {error_msg}")
        error_payload = json.dumps({
            "error": "Model yanıtı alınamadı. Lütfen ayarları kontrol edip tekrar deneyin.",
            "llm_call_failed": True
        }, ensure_ascii=False)
        yield f"data: {error_payload}\n\n"
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
    - customer: Customer panel context
    - business: Business panel context (default)
    - courier: Courier panel context
    - multi: Cross-panel analysis
    
    **Mode options**:
    - metrics: Focus on metrics analysis
    - summary: General summary with RCA (default)
    - patch: Include code examples and fixes
    
    Returns streaming SSE response with proper Turkish messages.
    """
    db = get_db()
    
    # Validate scope
    valid_scopes = ["customer", "business", "courier", "multi"]
    if request.scope not in valid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Geçersiz panel seçimi. Geçerli değerler: {', '.join(valid_scopes)}"
        )
    
    # Get AI settings
    settings_doc = await db.admin_settings_ai.find_one({"id": "ai_settings_default"})
    settings = settings_doc if settings_doc else {}
    
    # Rate limiting check (simplified - log for monitoring)
    print(f"📊 AI Query: user={current_user.get('email')}, scope={request.scope}, mode={request.mode}, window={request.time_window_minutes}dk")
    
    # Build panel-aware context
    context = await build_panel_context(
        request.scope,
        request.time_window_minutes,
        request.include_logs,
        db
    )
    
    # Audit log
    try:
        await db.ai_audit_logs.insert_one({
            "user_id": current_user.get("id", current_user.get("_id")),
            "user_email": current_user.get("email"),
            "question": request.question[:200],  # Truncate
            "scope": request.scope,
            "mode": request.mode,
            "time_window_minutes": request.time_window_minutes,
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception as e:
        print(f"⚠️ Audit log error: {str(e)}")
    
    # Return streaming response with proper headers
    return StreamingResponse(
        stream_ai_response(request.question, request.scope, context, request.mode, settings, request.provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Connection": "keep-alive"
        }
    )


@router.get("/ingest/health", summary="AI Log Ingest Health Check")
async def ai_ingest_health(
    current_user: dict = Depends(get_admin_user)
):
    """
    Check AI log ingest health per panel
    
    **RBAC**: SuperAdmin & Operasyon only
    
    Returns count of logs per panel in last 15 minutes.
    """
    db = get_db()
    
    # Calculate 15 min ago
    now = datetime.now(timezone.utc)
    fifteen_min_ago = now - timedelta(minutes=15)
    
    try:
        # Count logs per app in last 15 min
        apps_health = {}
        
        for app in ["customer", "business", "courier", "admin"]:
            count = await db.ai_logs.count_documents({
                "app": app,
                "timestamp": {"$gte": fifteen_min_ago}
            })
            
            # Get last timestamp
            last_log = await db.ai_logs.find_one(
                {"app": app},
                sort=[("timestamp", -1)]
            )
            
            apps_health[app] = {
                "count_15m": count,
                "last_ts": last_log.get("timestamp").isoformat() if last_log else None
            }
        
        return {
            "ok": True,
            "apps": apps_health,
            "checked_at": now.isoformat()
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "checked_at": now.isoformat()
        }


@router.get("/provider/status", summary="AI Provider Status")
async def ai_provider_status(
    current_user: dict = Depends(get_admin_user)
):
    """
    Get AI provider status and availability
    
    **RBAC**: SuperAdmin & Operasyon only
    
    Returns status of both Emergent and OpenAI providers.
    """
    from ai_provider import get_provider_status, current_provider_meta
    
    status = get_provider_status()
    meta = current_provider_meta()
    
    return {
        "providers": status,
        "current": meta,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/selftest", summary="AI LLM Connection Self-Test")
async def ai_selftest(
    current_user: dict = Depends(get_admin_user)
):
    """
    Test LLM connection with a harmless prompt
    
    **RBAC**: SuperAdmin & Operasyon only
    
    Returns provider, model, and latency.
    """
    db = get_db()
    
    # Get AI settings
    settings_doc = await db.admin_settings_ai.find_one({"id": "ai_settings_default"})
    settings = settings_doc if settings_doc else {}
    
    start_time = datetime.now(timezone.utc)
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Determine API key and provider
        api_key = None
        provider = "emergent"
        model = settings.get("default_model", "gpt-4o-mini")
        
        if settings and settings.get("openai_api_key") and not settings.get("use_emergent_key", True):
            api_key = settings["openai_api_key"]
            provider = "openai_custom"
        else:
            api_key = os.environ.get("EMERGENT_LLM_KEY")
            provider = "emergent"
        
        if not api_key:
            return {
                "ok": False,
                "error": "API anahtarı yapılandırılmamış.",
                "provider": None,
                "model": None
            }
        
        # Create test chat
        test_chat = LlmChat(
            api_key=api_key,
            session_id=f"selftest_{current_user.get('email', 'unknown')}",
            system_message="Sen yardımcı bir asistansın."
        ).with_model("openai", model)
        
        # Send harmless test message
        test_message = UserMessage(text="Bu bir sağlık kontrolüdür. Sadece 'OK' ile yanıt ver.")
        response = await test_chat.send_message(test_message)
        
        # Calculate latency
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "ok": True,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "test_response": response[:50],  # First 50 chars
            "timestamp": end_time.isoformat()
        }
    
    except Exception as e:
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "ok": False,
            "error": str(e),
            "provider": provider if 'provider' in locals() else None,
            "model": model if 'model' in locals() else None,
            "latency_ms": latency_ms,
            "timestamp": end_time.isoformat()
        }
