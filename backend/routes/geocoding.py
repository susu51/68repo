"""
Geocoding Service Routes
Reverse geocoding for address validation
Uses Nominatim (OpenStreetMap) as primary, with fallback options
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import asyncio

router = APIRouter(prefix="/geocode", tags=["geocoding"])

class ReverseGeocodeRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class ReverseGeocodeResponse(BaseModel):
    il: str
    ilce: str
    mahalle: Optional[str] = None
    posta_kodu: Optional[str] = None
    formatted_address: str
    success: bool = True

@router.post("/reverse", response_model=ReverseGeocodeResponse)
async def reverse_geocode(request: ReverseGeocodeRequest):
    """
    Reverse geocode coordinates to Turkish address components
    Uses Nominatim (OSM) API
    """
    try:
        # Nominatim reverse geocoding
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": request.lat,
            "lon": request.lng,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "tr"
        }
        headers = {
            "User-Agent": "Kuryecini/1.0"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Geocoding service unavailable"
                )
            
            data = response.json()
            address = data.get("address", {})
            
            # Extract Turkish administrative levels
            # Nominatim returns: state (il), county/city (ilçe), suburb/neighbourhood (mahalle)
            il = (
                address.get("state") or 
                address.get("province") or 
                address.get("city") or
                ""
            )
            
            ilce = (
                address.get("county") or
                address.get("town") or
                address.get("city_district") or
                address.get("municipality") or
                ""
            )
            
            mahalle = (
                address.get("suburb") or
                address.get("neighbourhood") or
                address.get("quarter") or
                ""
            )
            
            posta_kodu = address.get("postcode")
            
            # Validation: Must have at least il and ilce
            if not il or not ilce:
                raise HTTPException(
                    status_code=400,
                    detail="Could not determine city (il) and district (ilçe). Please enter manually."
                )
            
            # Check if in Turkey (basic validation)
            country = address.get("country", "").lower()
            if "turkey" not in country and "türkiye" not in country:
                raise HTTPException(
                    status_code=400,
                    detail="Location is outside Turkey. Please select a location within Turkey."
                )
            
            formatted_address = data.get("display_name", "")
            
            return ReverseGeocodeResponse(
                il=il.strip(),
                ilce=ilce.strip(),
                mahalle=mahalle.strip() if mahalle else None,
                posta_kodu=posta_kodu,
                formatted_address=formatted_address,
                success=True
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding failed: {str(e)}"
        )

@router.get("/health")
async def geocoding_health():
    """Check if geocoding service is accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/status",
                headers={"User-Agent": "Kuryecini/1.0"}
            )
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "service": "nominatim"
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "service": "nominatim",
            "error": str(e)
        }
