"""
Database Configuration - Environment-based with Timeout Parameters
Eliminates hardcoded MongoDB URLs
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import urlparse, urlencode, urlunparse, parse_qs
from config.settings import settings


def _add_connection_params(url: str) -> str:
    """
    Add connection timeout parameters to MongoDB URL
    Preserves existing parameters
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Add or update parameters
    params = {
        "appname": settings.APP_NAME,
        "connectTimeoutMS": str(settings.DB_CONNECT_TIMEOUT_MS),
        "serverSelectionTimeoutMS": str(settings.DB_SERVER_SELECTION_TIMEOUT_MS),
    }
    
    # Merge with existing params (don't override if already set)
    for key, value in params.items():
        if key.lower() not in [k.lower() for k in query_params.keys()]:
            query_params[key] = [value]
    
    # Rebuild query string
    query_items = []
    for key, values in query_params.items():
        for value in values:
            query_items.append(f"{key}={value}")
    
    new_query = "&".join(query_items)
    
    # Rebuild URL
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


# Get URL from environment (never hardcoded)
DATABASE_URL = _add_connection_params(settings.DATABASE_URL)

# Create MongoDB client with configured parameters
client = AsyncIOMotorClient(DATABASE_URL)

# Get database (extract name from URL or use default)
def get_database():
    """Get database instance from client"""
    # Try to get default database from URL
    db = client.get_default_database()
    if db is not None:
        return db
    
    # Extract database name from URL
    parsed = urlparse(settings.DATABASE_URL)
    if parsed.path and len(parsed.path) > 1:
        db_name = parsed.path.lstrip("/").split("?")[0]
        return client[db_name]
    
    # Fallback to app name
    return client[settings.APP_NAME]


db = get_database()
