"""
Address Management with City-Strict Validation
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
# Import auth dependency (adjust path as needed)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_cookie import get_current_user_from_cookie

# Turkish slug normalization
def normalize_turkish_slug(text):
    """Convert Turkish text to URL-safe slug"""
    if not text:
        return ""
    
    char_map = {
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g', 
        'ı': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u'
    }
    
    result = ""
    for char in text:
        result += char_map.get(char, char)
    
    return result.lower().replace(' ', '-')

# Pydantic models - Updated for full address system
class AddressCreate(BaseModel):
    adres_basligi: str = Field(..., description="Address title/label like 'Ev', 'İş'")
    alici_adsoyad: str = Field(..., description="Recipient full name")
    telefon: str = Field(..., description="Contact phone number")
    acik_adres: str = Field(..., description="Full open address text")
    il: str = Field(..., description="Province/City (required, e.g., 'Niğde')")
    ilce: str = Field(..., description="District (required, e.g., 'Merkez')")
    mahalle: str = Field(..., description="Neighborhood/Quarter")
    posta_kodu: Optional[str] = Field(None, description="Postal code")
    kat_daire: Optional[str] = Field(None, description="Floor/Apartment number")
    lat: float = Field(..., ge=-90, le=90, description="Latitude (required)")
    lng: float = Field(..., ge=-180, le=180, description="Longitude (required)")
    is_default: bool = Field(default=False, description="Set as default address")
    
    # Backward compatibility fields (optional)
    label: Optional[str] = None  # Maps to adres_basligi
    full: Optional[str] = None   # Maps to acik_adres
    city: Optional[str] = None   # Maps to il
    district: Optional[str] = None  # Maps to ilce

class AddressUpdate(BaseModel):
    adres_basligi: Optional[str] = None
    alici_adsoyad: Optional[str] = None
    telefon: Optional[str] = None
    acik_adres: Optional[str] = None
    il: Optional[str] = None
    ilce: Optional[str] = None
    mahalle: Optional[str] = None
    posta_kodu: Optional[str] = None
    kat_daire: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    is_default: Optional[bool] = None
    
    # Backward compatibility
    label: Optional[str] = None
    full: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None

class AddressResponse(BaseModel):
    id: str
    adres_basligi: str
    alici_adsoyad: str
    telefon: str
    acik_adres: str
    il: str
    ilce: str
    mahalle: str
    posta_kodu: Optional[str] = None
    kat_daire: Optional[str] = None
    lat: float
    lng: float
    is_default: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Backward compatibility fields
    label: Optional[str] = None
    full: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None

router = APIRouter(prefix="/me", tags=["addresses"])

# Global database client (will be set from main app)
db = None

def set_db_client(database):
    global db
    db = database

@router.post("/addresses", response_model=dict, status_code=201)
async def create_address(
    address_data: AddressCreate,
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Create new address with full Turkish address system
    Requires: il, ilçe, mahalle, lat/lng validation
    NO DEFAULT TO ISTANBUL - all fields must be explicitly provided
    """
    
    # Map backward compatibility fields
    il = address_data.il or address_data.city
    ilce = address_data.ilce or address_data.district
    adres_basligi = address_data.adres_basligi or address_data.label
    acik_adres = address_data.acik_adres or address_data.full
    
    # Validate REQUIRED fields
    if not il or not ilce or not adres_basligi or not acik_adres:
        raise HTTPException(
            status_code=422, 
            detail="il (city), ilçe (district), adres_basligi (label), and acik_adres (full address) are required"
        )
    
    if not address_data.mahalle:
        raise HTTPException(
            status_code=422,
            detail="mahalle (neighborhood) is required"
        )
    
    if not address_data.alici_adsoyad or not address_data.telefon:
        raise HTTPException(
            status_code=422,
            detail="alici_adsoyad (recipient name) and telefon (phone) are required"
        )
    
    if address_data.lat is None or address_data.lng is None:
        raise HTTPException(
            status_code=422,
            detail="lat and lng coordinates are required"
        )
    
    # CRITICAL: Prevent Istanbul default - explicitly check
    if il.lower().strip() in ['istanbul', 'İstanbul'] and not address_data.lat:
        raise HTTPException(
            status_code=422,
            detail="İstanbul adresi için konum koordinatları zorunludur"
        )
    
    # If setting as default, unset other defaults
    if address_data.is_default:
        await db.addresses.update_many(
            {"user_id": current_user["id"]},
            {"$set": {"is_default": False}}
        )
    
    # Create address document with NEW schema
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    
    address_doc = {
        "_id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "adres_basligi": adres_basligi,
        "alici_adsoyad": address_data.alici_adsoyad,
        "telefon": address_data.telefon,
        "acik_adres": acik_adres,
        "il": il,
        "ilce": ilce,
        "mahalle": address_data.mahalle,
        "posta_kodu": address_data.posta_kodu,
        "kat_daire": address_data.kat_daire,
        "location": {
            "type": "Point",
            "coordinates": [address_data.lng, address_data.lat]  # [lng, lat]
        },
        "is_default": address_data.is_default,
        "created_at": now,
        "updated_at": now,
        # Backward compatibility fields
        "label": adres_basligi,
        "full": acik_adres,
        "city": il,
        "district": ilce
    }
    
    result = await db.addresses.insert_one(address_doc)
    
    return {
        "success": True,
        "message": "Address created successfully",
        "address_id": address_doc["_id"]
    }

@router.get("/addresses", response_model=List[AddressResponse])
async def get_addresses(current_user = Depends(get_current_user_from_cookie)):
    """Get user addresses, default first - NEW schema with backward compat"""
    
    addresses = await db.addresses.find(
        {"user_id": current_user["id"]}
    ).sort("is_default", -1).to_list(length=None)
    
    result = []
    for addr in addresses:
        # Handle ObjectId conversion
        addr_id = str(addr.get("_id", addr.get("id", "")))
        
        # Handle coordinates - check both GeoJSON and direct lat/lng fields
        if addr.get("location") and addr["location"].get("coordinates"):
            coords = addr["location"]["coordinates"]
            lng_val = float(coords[0]) if len(coords) > 0 and coords[0] is not None else 0.0
            lat_val = float(coords[1]) if len(coords) > 1 and coords[1] is not None else 0.0
        else:
            lat_raw = addr.get("lat", 0)
            lng_raw = addr.get("lng", 0)
            lat_val = float(lat_raw) if lat_raw is not None else 0.0
            lng_val = float(lng_raw) if lng_raw is not None else 0.0
        
        # Map new schema fields (with backward compat)
        adres_basligi = addr.get("adres_basligi") or addr.get("label", "")
        acik_adres = addr.get("acik_adres") or addr.get("full", "")
        il = addr.get("il") or addr.get("city", "")
        ilce = addr.get("ilce") or addr.get("district", "")
        
        # Convert datetime objects to strings
        created_at_str = None
        updated_at_str = None
        if addr.get("created_at"):
            created_at_obj = addr.get("created_at")
            if hasattr(created_at_obj, 'isoformat'):
                created_at_str = created_at_obj.isoformat()
            else:
                created_at_str = str(created_at_obj)
        
        if addr.get("updated_at"):
            updated_at_obj = addr.get("updated_at")
            if hasattr(updated_at_obj, 'isoformat'):
                updated_at_str = updated_at_obj.isoformat()
            else:
                updated_at_str = str(updated_at_obj)
        
        result.append(AddressResponse(
            id=addr_id,
            adres_basligi=adres_basligi,
            alici_adsoyad=addr.get("alici_adsoyad", ""),
            telefon=addr.get("telefon", ""),
            acik_adres=acik_adres,
            il=il,
            ilce=ilce,
            mahalle=addr.get("mahalle", ""),
            posta_kodu=addr.get("posta_kodu"),
            kat_daire=addr.get("kat_daire"),
            lat=lat_val,
            lng=lng_val,
            is_default=addr.get("is_default", False),
            created_at=created_at_str,
            updated_at=updated_at_str,
            # Backward compat
            label=adres_basligi,
            full=acik_adres,
            city=il,
            district=ilce
        ))
    
    return result

@router.patch("/addresses/{address_id}")
async def update_address(
    address_id: str,
    address_data: AddressUpdate,
    current_user = Depends(get_current_user_from_cookie)
):
    """Update address with validation"""
    
    # Check ownership
    existing = await db.addresses.find_one({
        "_id": address_id,
        "user_id": current_user["id"]
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="Address not found")
    
    # Build update document
    update_doc = {}
    
    if address_data.label is not None:
        update_doc["label"] = address_data.label
    if address_data.full is not None:
        update_doc["full"] = address_data.full
    if address_data.city is not None:
        update_doc["city"] = address_data.city
        update_doc["city_slug"] = normalize_turkish_slug(address_data.city)
    if address_data.district is not None:
        update_doc["district"] = address_data.district
        update_doc["district_slug"] = normalize_turkish_slug(address_data.district)
    
    # Update location if coordinates provided
    if address_data.lat is not None and address_data.lng is not None:
        update_doc["location"] = {
            "type": "Point",
            "coordinates": [address_data.lng, address_data.lat]
        }
    
    # Handle default setting
    if address_data.is_default is True:
        # Unset other defaults first
        await db.addresses.update_many(
            {"user_id": current_user["id"]},
            {"$set": {"is_default": False}}
        )
        update_doc["is_default"] = True
    elif address_data.is_default is False:
        update_doc["is_default"] = False
    
    if update_doc:
        await db.addresses.update_one(
            {"_id": address_id},
            {"$set": update_doc}
        )
    
    return {"success": True, "message": "Address updated successfully"}

@router.patch("/addresses/{address_id}/default")
async def set_default_address(
    address_id: str,
    current_user = Depends(get_current_user_from_cookie)
):
    """Set address as default"""
    
    # Check if address exists and belongs to user
    address = await db.addresses.find_one({
        "_id": address_id,
        "user_id": current_user["id"]
    })
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    # Unset all other defaults for this user
    await db.addresses.update_many(
        {"user_id": current_user["id"]},
        {"$set": {"is_default": False}}
    )
    
    # Set this address as default
    await db.addresses.update_one(
        {"_id": address_id},
        {"$set": {"is_default": True}}
    )
    
    return {"success": True, "message": "Default address updated"}

@router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user = Depends(get_current_user_from_cookie)
):
    """Delete user address"""
    
    result = await db.addresses.delete_one({
        "_id": address_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
    
    return {"success": True, "message": "Address deleted successfully"}