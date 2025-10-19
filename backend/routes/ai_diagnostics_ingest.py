"""
AI Diagnostics Log Ingestion - Phase 1
Centralized log collection with PII redaction
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import os

from models_package.ai_diagnostics import (
    LogIngestRequest, redact_pii, compute_fingerprint,
    classify_severity, extract_tags, AppType, LogLevel
)

router = APIRouter(prefix="/admin/logs", tags=["ai-diagnostics"])

# Service key authentication
ADMIN_SERVICE_KEY = os.getenv("ADMIN_SERVICE_KEY", "change_me")

async def verify_service_key(authorization: Optional[str] = Header(None)):
    """Verify service key for log ingestion"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Expected: "Bearer <key>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = parts[1]
    if token != ADMIN_SERVICE_KEY:
        raise HTTPException(status_code=403, detail="Invalid service key")
    
    return True

@router.post("/ingest")
async def ingest_logs(
    log_entry: LogIngestRequest,
    x_app_name: str = Header(..., alias="X-App-Name"),
    _auth: bool = Depends(verify_service_key)
):
    """
    Ingest log entry with PII redaction and clustering
    
    Headers:
    - Authorization: Bearer <ADMIN_SERVICE_KEY>
    - X-App-Name: customer|business|courier|admin
    """
    from server import db
    
    try:
        # Validate app name
        try:
            app = AppType(x_app_name.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid app name: {x_app_name}. Must be: customer, business, courier, admin"
            )
        
        # Redact PII
        redacted_message = redact_pii(log_entry.message)
        redacted_stack = redact_pii(log_entry.stack) if log_entry.stack else None
        redacted_meta = {k: redact_pii(str(v)) if isinstance(v, str) else v 
                        for k, v in log_entry.meta.items()}
        
        # Compute fingerprint for clustering
        fingerprint = compute_fingerprint(
            log_entry.message,
            log_entry.stack,
            log_entry.route
        )
        
        # Classify severity
        severity = classify_severity(
            log_entry.level,
            log_entry.message,
            log_entry.stack
        )
        
        # Extract tags
        tags = extract_tags(
            log_entry.message,
            log_entry.route,
            log_entry.meta
        )
        tags.extend(log_entry.tags)
        tags = list(set(tags))
        
        # Create log document
        now = datetime.now(timezone.utc)
        log_id = str(uuid.uuid4())
        
        log_doc = {
            "_id": log_id,
            "app": app.value,
            "level": log_entry.level.upper(),
            "ts": now,
            "route": log_entry.route,
            "code_location": log_entry.code_location,
            "message": redacted_message,
            "stack": redacted_stack,
            "meta": redacted_meta,
            "request_id": log_entry.request_id,
            "user_id": log_entry.user_id,
            "redacted": True,
            "fingerprint": fingerprint,
            "deployment": log_entry.deployment,
            "tags": tags
        }
        
        # Insert log
        await db.ai_logs.insert_one(log_doc)
        
        print(f"✅ Ingested log: {log_id} from {app.value} (fingerprint: {fingerprint})")
        
        # Update cluster
        await update_cluster(
            db=db,
            fingerprint=fingerprint,
            app=app.value,
            level=log_entry.level.upper(),
            message=redacted_message,
            stack=redacted_stack,
            severity=severity,
            user_id=log_entry.user_id,
            now=now
        )
        
        # Audit log
        await db.admin_audit_log.insert_one({
            "_id": str(uuid.uuid4()),
            "action": "ai_log_ingest",
            "app": app.value,
            "fingerprint": fingerprint,
            "level": log_entry.level,
            "ts": now,
            "meta": {"log_id": log_id}
        })
        
        return {
            "ok": True,
            "log_id": log_id,
            "fingerprint": fingerprint,
            "severity": severity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error ingesting log: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Log ingestion failed: {str(e)}"
        )

async def update_cluster(
    db,
    fingerprint: str,
    app: str,
    level: str,
    message: str,
    stack: Optional[str],
    severity: str,
    user_id: Optional[str],
    now: datetime
):
    """
    Update or create cluster for this fingerprint
    """
    try:
        # Find existing cluster
        cluster = await db.ai_clusters.find_one({"fingerprint": fingerprint})
        
        if cluster:
            # Update existing cluster
            update_doc = {
                "$set": {
                    "last_seen": now,
                    "severity": severity  # Update to latest severity
                },
                "$inc": {
                    "count_24h": 1
                },
                "$addToSet": {
                    "apps": app
                }
            }
            
            # Track unique users
            if user_id and user_id not in cluster.get("affected_user_ids", []):
                update_doc["$addToSet"]["affected_user_ids"] = user_id
                update_doc["$inc"]["affected_users"] = 1
            
            await db.ai_clusters.update_one(
                {"fingerprint": fingerprint},
                update_doc
            )
            
            print(f"📊 Updated cluster: {fingerprint} (count_24h: {cluster.get('count_24h', 0) + 1})")
            
        else:
            # Create new cluster
            # Extract title from message (first 100 chars)
            title = message[:100] + "..." if len(message) > 100 else message
            
            # Top stack frame
            top_stack = None
            if stack:
                lines = [l.strip() for l in stack.split('\n') if l.strip()]
                top_stack = lines[0] if lines else None
            
            cluster_doc = {
                "_id": str(uuid.uuid4()),
                "fingerprint": fingerprint,
                "title": title,
                "sample_message": message,
                "top_stack": top_stack,
                "apps": [app],
                "first_seen": now,
                "last_seen": now,
                "severity": severity,
                "count_24h": 1,
                "affected_users": 1 if user_id else 0,
                "affected_user_ids": [user_id] if user_id else [],
                "rca_summary": None,
                "suggested_fix": None
            }
            
            await db.ai_clusters.insert_one(cluster_doc)
            
            print(f"🆕 Created cluster: {fingerprint} ({severity})")
        
        # Reset count_24h for old clusters (TTL-like behavior)
        cutoff = now - timedelta(hours=24)
        await db.ai_clusters.update_many(
            {"last_seen": {"$lt": cutoff}, "count_24h": {"$gt": 0}},
            {"$set": {"count_24h": 0}}
        )
        
    except Exception as e:
        print(f"⚠️ Error updating cluster: {e}")
        # Don't fail the whole ingestion if clustering fails
