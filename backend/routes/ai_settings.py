"""
AI Settings API Routes
Manages AI Diagnostics Panel configuration (OpenAI keys, redaction rules, rate limits)
RBAC: SuperAdmin & Operasyon only
"""

from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Import models
from models_package.ai_settings import (
    AISettings,
    AISettingsUpdate,
    AISettingsResponse,
    RedactionRule
)

# Import auth dependencies
from auth_cookie import get_admin_user

router = APIRouter(prefix="/admin/ai/settings", tags=["AI Settings"])
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


@router.get("", response_model=AISettingsResponse, summary="Get AI Settings")
async def get_ai_settings(
    current_user: dict = Depends(get_admin_user)
):
    """
    Get current AI Diagnostics Panel settings
    
    **RBAC**: SuperAdmin & Operasyon only
    
    Returns masked settings (API keys are shown as configured/not configured)
    """
    db = get_db()
    
    # Get settings from database
    settings_doc = await db.admin_settings_ai.find_one({"id": "ai_settings_default"})
    
    if not settings_doc:
        # Return default settings if not found
        default_settings = AISettings()
        return AISettingsResponse(
            id=default_settings.id,
            openai_api_key_configured=False,
            use_emergent_key=default_settings.use_emergent_key,
            default_model=default_settings.default_model,
            default_time_window_minutes=default_settings.default_time_window_minutes,
            rate_limit_per_min=default_settings.rate_limit_per_min,
            redact_rules=default_settings.redact_rules,
            updated_at=default_settings.updated_at,
            updated_by=None
        )
    
    # Return masked settings
    return AISettingsResponse(
        id=settings_doc.get("id", "ai_settings_default"),
        openai_api_key_configured=bool(settings_doc.get("openai_api_key")),
        use_emergent_key=settings_doc.get("use_emergent_key", True),
        default_model=settings_doc.get("default_model", "gpt-4o-mini"),
        default_time_window_minutes=settings_doc.get("default_time_window_minutes", 60),
        rate_limit_per_min=settings_doc.get("rate_limit_per_min", 6),
        redact_rules=[RedactionRule(**rule) for rule in settings_doc.get("redact_rules", [])],
        updated_at=settings_doc.get("updated_at", datetime.now(timezone.utc)),
        updated_by=settings_doc.get("updated_by")
    )


@router.put("", response_model=AISettingsResponse, summary="Update AI Settings")
async def update_ai_settings(
    settings_update: AISettingsUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """
    Update AI Diagnostics Panel settings
    
    **RBAC**: SuperAdmin & Operasyon only
    
    Allows admins to:
    - Set custom OpenAI API key (overrides Emergent LLM Key)
    - Configure default time windows
    - Adjust rate limits
    - Enable/disable PII redaction rules
    """
    db = get_db()
    
    # Get current settings
    current_settings_doc = await db.admin_settings_ai.find_one({"id": "ai_settings_default"})
    
    if not current_settings_doc:
        # Create default settings
        current_settings = AISettings()
        current_settings_dict = current_settings.model_dump()
    else:
        current_settings_dict = current_settings_doc
    
    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    
    # Handle redaction rules (convert to dict format)
    if "redact_rules" in update_data and update_data["redact_rules"]:
        update_data["redact_rules"] = [rule.model_dump() for rule in update_data["redact_rules"]]
    
    # Update metadata
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = current_user.get("id", current_user.get("_id"))
    
    # Merge updates
    current_settings_dict.update(update_data)
    
    # Upsert to database
    await db.admin_settings_ai.update_one(
        {"id": "ai_settings_default"},
        {"$set": current_settings_dict},
        upsert=True
    )
    
    # Return masked response
    return AISettingsResponse(
        id="ai_settings_default",
        openai_api_key_configured=bool(current_settings_dict.get("openai_api_key")),
        use_emergent_key=current_settings_dict.get("use_emergent_key", True),
        default_model=current_settings_dict.get("default_model", "gpt-4o-mini"),
        default_time_window_minutes=current_settings_dict.get("default_time_window_minutes", 60),
        rate_limit_per_min=current_settings_dict.get("rate_limit_per_min", 6),
        redact_rules=[RedactionRule(**rule) for rule in current_settings_dict.get("redact_rules", [])],
        updated_at=current_settings_dict.get("updated_at"),
        updated_by=current_settings_dict.get("updated_by")
    )


@router.post("/test", summary="Test OpenAI Connection")
async def test_openai_connection(
    current_user: dict = Depends(get_admin_user)
):
    """
    Test OpenAI API connection with current settings
    
    **RBAC**: SuperAdmin & Operasyon only
    
    Makes a simple test request to verify API key is working
    """
    db = get_db()
    
    # Get current settings
    settings_doc = await db.admin_settings_ai.find_one({"id": "ai_settings_default"})
    
    # Determine which API key to use
    api_key = None
    key_source = "emergent"
    
    if settings_doc and settings_doc.get("openai_api_key") and not settings_doc.get("use_emergent_key", True):
        api_key = settings_doc["openai_api_key"]
        key_source = "custom"
    else:
        # Use Emergent LLM Key
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        key_source = "emergent"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No API key configured. Please set OpenAI API key or ensure Emergent LLM Key is available."
        )
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Create test chat with minimal context
        test_chat = LlmChat(
            api_key=api_key,
            session_id=f"test_{current_user.get('id', 'unknown')}",
            system_message="You are a helpful assistant."
        ).with_model("openai", settings_doc.get("default_model", "gpt-4o-mini") if settings_doc else "gpt-4o-mini")
        
        # Send test message
        test_message = UserMessage(text="Test connection. Reply with 'OK' only.")
        response = await test_chat.send_message(test_message)
        
        return {
            "success": True,
            "message": "OpenAI API connection successful",
            "key_source": key_source,
            "model": settings_doc.get("default_model", "gpt-4o-mini") if settings_doc else "gpt-4o-mini",
            "test_response": response[:100]  # First 100 chars
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OpenAI API test failed: {str(e)}"
        )
