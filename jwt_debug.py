#!/usr/bin/env python3
"""
Debug JWT token
"""

import jwt
import json
from datetime import datetime

# JWT token from the response
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3ZDE1MDUxNi05M2QzLTRjMDktYTZlZC04ZWUyMDY2NDNiZDciLCJleHAiOjE3NjA1MTY3NzYsImlhdCI6MTc2MDUxNTg3Nn0.7hyMDxyLftSiULktYs7WFXnPPXHpMcXKt_s_xSO8DpM"

print("🔍 JWT Token Debug")
print("=" * 50)

# Decode without verification to see the payload
try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("JWT Payload:")
    print(json.dumps(decoded, indent=2))
    
    # Check expiration
    exp = decoded.get("exp")
    if exp:
        exp_date = datetime.fromtimestamp(exp)
        now = datetime.now()
        print(f"\nExpiration: {exp_date}")
        print(f"Current time: {now}")
        print(f"Token expired: {now > exp_date}")
    
except Exception as e:
    print(f"Error decoding JWT: {e}")

# Try to decode the header
try:
    header = jwt.get_unverified_header(token)
    print(f"\nJWT Header:")
    print(json.dumps(header, indent=2))
except Exception as e:
    print(f"Error decoding JWT header: {e}")