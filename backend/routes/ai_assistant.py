"""
Panel AI Assistant Backend Endpoint - HARDENED
Streaming Turkish AI responses with proper PII redaction and panel isolation
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
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
    # Extract database name from environment
    db_name = os.environ.get("DB_NAME")
    if not db_name:
        mongo_url = os.environ.get("MONGO_URL", "")
        if "/" in mongo_url:
            db_name = mongo_url.split("/")[-1].split("?")[0]
        else:
            db_name = "kuryecini"
    return router.db_client[db_name]


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
    ENHANCED: Proactive code assistant with structured responses
    """
    base_prompt = """
Sen bir Kod Asistanısın. Görevin: Kullanıcının sorununu anlamak, önce kendin dosyaları arayıp incelemek, sonra açıklamalı bir yanıt vermek.

**TEMEL KURALLAR:**
1. **Otomatik keşif**: Bağlam eksikse kendin list_files ve grep çalıştır
   - Örnek: @app.get("/restaurants"), isletmeler, pymongo, motor, ObjectId, 404, [], CORSMiddleware gibi kalıpları ara
2. **Dosya:Satır göster**: Hangi satırda hata gördüysen mutlaka belirt (backend/routes/businesses.py:12)
3. **Patch formatı**: Değişiklikleri mutlaka unified diff ile öner (+++ b/..., --- a/...)
4. **Test zorunlu**: En az iki test (boş sonuç + mutlu yol)
5. **Metrik/Alarm**: Ölçülebilir metrik öner (örn. latency_p95 < 300ms, error_rate < %1)
6. **İnsansı açıklama**: Teknik ama sohbet tarzı açıkla; kuru JSON değil
7. **Sadece öneri**: Dosya değiştirmezsin, dış sisteme yazmazsın

**YANITLARINI HER ZAMAN ŞU BAŞLIKLARLA VER:**

## Özet / Neyi Fark Ettim
(Sorunu kısaca özetle, hangi dosya:satır'da bulundu)

## Kısa RCA (kök neden)
(Neden oluştu? Hangi konfigürasyon/kod pattern sorumlu?)

## Hızlı Çözümler (hemen)
(Anında uygulanabilir adımlar - env değişkeni, config, kod değişikliği)

## Kod Örneği / Patch
(Unified diff formatında, dosya yollarıyla)
```diff
--- a/backend/routes/orders.py
+++ b/backend/routes/orders.py
@@ -45,7 +45,7 @@
-    city = "Istanbul"  # hardcoded
+    city = request.city  # from request
```

## Testler
(Mutlu yol + hata senaryosu)
```python
def test_happy_path():
    # ...

def test_error_case():
    # ...
```

## İzleme / Metrikler
(Alarm eşikleriyle - örn: latency_p95 < 300ms uyarı ≥ 350ms)

## Kabul Kriterleri (DoD)
(Tamamlanma kriterleri - testler yeşil, metrik < target, vb.)

## Sonraki Adımlar
(Yapılması gerekenler - prod'a deploy, monitoring kurulumu, vb.)

"""
    
    # Panel-specific context
    panel_context = {
        "customer": """
**Panel: CUSTOMER (Müşteri)**
Odak: Restoran keşfi, sepet/checkout, kupon, sipariş takibi
Dosya kalıpları: customer, restaurant, menu, cart, order, checkout
""",
        "business": """
**Panel: BUSINESS (İşletme)**
Odak: Sipariş liste/onay, menü yönetimi, çalışma saatleri, SLA
Dosya kalıpları: business, order_confirm, menu_manager, working_hours
""",
        "courier": """
**Panel: COURIER (Kurye)**
Odak: Görev kabul, WS bağlantısı, rota/konum, ETA
Dosya kalıpları: courier, task, location, route, delivery
""",
        "multi": """
**Panel: MULTI (Çapraz Analiz)**
Odak: Üç paneli karşılaştır, çapraz etkileri analiz et
Dosya kalıpları: Tüm panellerin dosyalarını incele
"""
    }
    
    # Mode-specific instructions
    mode_instructions = {
        "metrics": """
**MOD: METRICS**
Metrik yorumlamaya odaklan. Sayısal değerleri analiz et, trend yorumu yap.
p95, p50, error_rate, throughput gibi metriklere öncelik ver.
""",
        "summary": """
**MOD: SUMMARY**
Log ve cluster özetleri ile Kök Neden Analizi (RCA).
Spesifik dosya/satır referansları ver.
Hangi kod pattern'i sorumlu olduğunu açıkla.
""",
        "patch": """
**MOD: PATCH**
Kök Neden Analizi (RCA) + Unified Diff + Test.
- Sadece bağlamda verilen dosyalardan örnekle
- Dosya yollarını tam belirt (backend/routes/orders.py)
- Unified diff formatı zorunlu
- En az 2 test yaz (mutlu yol + hata)
- pytest veya jest kullan
"""
    }
    
    # PII protection reminder
    pii_reminder = """
**PII KORUMA:**
<MASK:EMAIL>, <MASK:PHONE>, <MASK:IBAN>, <MASK:TOKEN>, <MASK:CARD>, <MASK:ADDR> maskelerini asla açma.
Örneklerde gerçek PII kullanma.
"""
    
    full_prompt = (
        base_prompt +
        panel_context.get(scope, panel_context["business"]) +
        mode_instructions.get(mode, mode_instructions["summary"]) +
        pii_reminder
    )
    
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


# ==================== AI Dev Tools ====================

@router.get("/dev/list_files", summary="List Repository Files")
async def dev_list_files(
    prefix: str = "",
    current_user: dict = Depends(get_admin_user)
):
    """
    List all text files in repository
    
    **RBAC**: SuperAdmin & Operasyon only
    **READ-ONLY**: No file modifications
    
    Args:
        prefix: Filter files by path prefix
    """
    from ai_tools_extra import list_files
    
    try:
        files = await list_files(prefix)
        return {
            "files": files,
            "count": len(files),
            "prefix": prefix
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dosya listesi alınamadı: {str(e)}"
        )


@router.get("/dev/grep", summary="Search Files (Grep)")
async def dev_grep(
    pattern: str,
    prefix: str = "",
    current_user: dict = Depends(get_admin_user)
):
    """
    Search for pattern in files (grep-like)
    
    **RBAC**: SuperAdmin & Operasyon only
    **READ-ONLY**: No file modifications
    
    Args:
        pattern: Regex pattern to search
        prefix: Filter files by path prefix
    """
    from ai_tools_extra import grep
    
    try:
        hits = await grep(pattern, prefix)
        return {
            "hits": hits,
            "count": len(hits),
            "pattern": pattern,
            "prefix": prefix
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arama başarısız: {str(e)}"
        )


@router.get("/dev/ast_outline", summary="Python AST Outline")
async def dev_ast_outline(
    path: str,
    current_user: dict = Depends(get_admin_user)
):
    """
    Get AST outline of Python file (classes and functions)
    
    **RBAC**: SuperAdmin & Operasyon only
    **READ-ONLY**: No file modifications
    
    Args:
        path: Relative path to Python file
    """
    from ai_tools_extra import ast_outline_py
    
    try:
        outline = await ast_outline_py(path)
        return {
            "outline": outline,
            "path": path
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AST analizi başarısız: {str(e)}"
        )



# ==================== KURYECINI OPS CO-PILOT ====================

class AssistRequest(BaseModel):
    """Kuryecini Ops Co-Pilot request"""
    panel: Literal["müşteri", "işletme", "kurye", "admin", "multi"] = Field(default="müşteri", description="Panel scope")
    message: str = Field(..., min_length=1, max_length=2000, description="User question in Turkish")
    model: Optional[str] = Field(None, description="Model name (default: gpt-4o-mini)")


@router.post("/assist", summary="Kuryecini Ops Co-Pilot - 7-Block Structured Response")
async def ai_assist(
    request: AssistRequest,
    current_user: dict = Depends(get_admin_user)
):
    """
    Kuryecini Ops Co-Pilot - Structured diagnostic assistant
    
    **RBAC**: SuperAdmin & Operasyon only
    
    **Panel options**:
    - müşteri: Customer panel diagnostics
    - işletme: Business panel diagnostics
    - kurye: Courier panel diagnostics
    - admin: Admin panel diagnostics
    - multi: Cross-panel analysis
    
    **Response format** (7 blocks - ENFORCED):
    1. Hızlı Teşhis (Quick Diagnosis)
    2. Derin RCA (Root Cause Analysis)
    3. Kontrol Komutları (Verification Commands)
    4. Patch (Mini Code Fix)
    5. Test (Test Cases)
    6. İzleme & Alarm (Monitoring)
    7. DoD (Definition of Done)
    
    Returns plain text (Markdown) with structured sections.
    """
    try:
        # Import utilities
        from routes.ai_utils import load_system_prompt, build_and_inject_context, ask_llm
        
        # Load and prepare system prompt
        system_prompt = load_system_prompt()
        system_prompt_with_ctx = build_and_inject_context(system_prompt, request.panel)
        
        # Log request (no PII)
        print(f"🛠️ Ops Co-Pilot: user={current_user.get('email')}, panel={request.panel}, model={request.model or 'gpt-4o-mini'}")
        
        # Get LLM response
        answer = ask_llm(system_prompt_with_ctx, request.message, request.model)
        
        # Audit log
        try:
            db = get_db()
            await db.ai_audit_logs.insert_one({
                "user_id": current_user.get("id", current_user.get("_id")),
                "user_email": current_user.get("email"),
                "question": request.message[:200],
                "panel": request.panel,
                "mode": "co-pilot",
                "timestamp": datetime.now(timezone.utc)
            })
        except Exception as e:
            print(f"⚠️ Audit log error: {str(e)}")
        
        # Return plain text response
        return {"response": answer, "panel": request.panel}
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ops Co-Pilot Error: {error_msg}")
        
        # Return error in 7-block format
        error_response = f"""# Hızlı Teşhis
• Durum: Asistan çağrısı hata verdi.
• Etki: Yanıt üretilemedi.
• Öncelik: P1

# Derin RCA (olasılık matrisi)
| Neden | Panel | Kanıt/İpucu | Olasılık | Nasıl Doğrularım |
|---|---|---|---|---|
| API anahtarı eksik | tüm | OPENAI_API_KEY yok | Yüksek | env_list |
| Ağ/timeout | tüm | ECONNRESET/ETIMEDOUT | Orta | tekrar dene |
| Model hatası | tüm | {error_msg[:100]} | Yüksek | logs |

# Kontrol Komutları (Kopyala-Çalıştır)
```bash
echo "CHECK OPENAI_API_KEY && network"
tail -n 50 /var/log/supervisor/backend.err.log
```

# Patch (Mini)
— 

# Test
```bash
curl -X POST /api/admin/ai/assist -d '{{"panel":"müşteri","message":"ping"}}'
```

# İzleme & Alarm
- Sentry: event.type:error route:/admin/ai/assist

# DoD
- 200 yanıt dönmeli.
"""
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"response": error_response, "error": error_msg}
        )


# ==================== TOOL ENDPOINTS ====================

@router.post("/tools/http_get", summary="Tool: HTTP GET")
async def tool_http_get_endpoint(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Execute HTTP GET tool (for manual tool usage)"""
    from routes.ai_utils import tool_http_get
    return tool_http_get(url, headers)


@router.post("/tools/logs_tail", summary="Tool: Logs Tail")
async def tool_logs_tail_endpoint(
    path: str = "/var/log/supervisor/backend.out.log",
    limit: int = 200,
    current_user: dict = Depends(get_admin_user)
):
    """Execute logs tail tool (for manual tool usage)"""
    from routes.ai_utils import tool_logs_tail
    return tool_logs_tail(path, limit)


@router.post("/tools/db_query", summary="Tool: DB Query")
async def tool_db_query_endpoint(
    collection: str,
    action: str,
    filter: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Execute DB query tool (for manual tool usage)"""
    from routes.ai_utils import tool_db_query
    return tool_db_query(collection, action, filter)


@router.get("/tools/env_list", summary="Tool: Env List")
async def tool_env_list_endpoint(
    mask: bool = True,
    current_user: dict = Depends(get_admin_user)
):
    """Execute env list tool (for manual tool usage)"""
    from routes.ai_utils import tool_env_list
    return tool_env_list(mask)
