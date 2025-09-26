import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from sms_service import sms_service
from config import settings
import logging

logger = logging.getLogger(__name__)

class OTPService:
    """OTP generation, validation and rate limiting service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.otp_collection = db.otps
        self.rate_limit_collection = db.rate_limits
    
    async def create_indexes(self):
        """Create necessary database indexes"""
        # OTP collection indexes
        await self.otp_collection.create_index([("phone", 1)])
        await self.otp_collection.create_index([("expires_at", 1)], expireAfterSeconds=0)
        await self.otp_collection.create_index([("created_at", 1)])
        
        # Rate limit collection indexes  
        await self.rate_limit_collection.create_index([("identifier", 1)])
        await self.rate_limit_collection.create_index([("reset_time", 1)], expireAfterSeconds=0)
    
    async def check_rate_limit(self, phone: str, ip_address: str) -> Dict[str, Any]:
        """
        Check rate limits for phone and IP
        Returns: {'allowed': bool, 'reason': str, 'retry_after': int}
        """
        current_time = datetime.utcnow()
        
        # Check phone rate limit (2 per minute)
        phone_identifier = f"phone:{phone}"
        phone_limit = await self.rate_limit_collection.find_one({
            "identifier": phone_identifier,
            "reset_time": {"$gt": current_time}
        })
        
        if phone_limit and phone_limit.get("count", 0) >= settings.rate_limit_per_phone_per_min:
            retry_after = int((phone_limit["reset_time"] - current_time).total_seconds())
            return {
                'allowed': False,
                'reason': 'Phone rate limit exceeded',
                'retry_after': retry_after
            }
        
        # Check IP rate limit (30 per minute) 
        ip_identifier = f"ip:{ip_address}"
        ip_limit = await self.rate_limit_collection.find_one({
            "identifier": ip_identifier,
            "reset_time": {"$gt": current_time}
        })
        
        if ip_limit and ip_limit.get("count", 0) >= settings.rate_limit_per_ip_per_min:
            retry_after = int((ip_limit["reset_time"] - current_time).total_seconds())
            return {
                'allowed': False,
                'reason': 'IP rate limit exceeded', 
                'retry_after': retry_after
            }
        
        return {'allowed': True, 'reason': '', 'retry_after': 0}
    
    async def increment_rate_limit(self, phone: str, ip_address: str):
        """Increment rate limit counters"""
        current_time = datetime.utcnow()
        reset_time = current_time + timedelta(minutes=1)
        
        # Increment phone counter
        phone_identifier = f"phone:{phone}"
        await self.rate_limit_collection.update_one(
            {
                "identifier": phone_identifier,
                "reset_time": {"$gt": current_time}
            },
            {
                "$inc": {"count": 1},
                "$setOnInsert": {"reset_time": reset_time}
            },
            upsert=True
        )
        
        # Increment IP counter
        ip_identifier = f"ip:{ip_address}"
        await self.rate_limit_collection.update_one(
            {
                "identifier": ip_identifier,
                "reset_time": {"$gt": current_time}
            },
            {
                "$inc": {"count": 1},
                "$setOnInsert": {"reset_time": reset_time}
            },
            upsert=True
        )
    
    async def check_otp_attempts(self, phone: str) -> Dict[str, Any]:
        """
        Check if phone is locked due to too many failed attempts
        Returns: {'locked': bool, 'attempts': int, 'unlock_time': datetime}
        """
        current_time = datetime.utcnow()
        
        # Find recent failed attempts
        lock_identifier = f"otp_lock:{phone}"
        lock_record = await self.rate_limit_collection.find_one({
            "identifier": lock_identifier,
            "reset_time": {"$gt": current_time}
        })
        
        if lock_record and lock_record.get("count", 0) >= settings.otp_max_attempts:
            return {
                'locked': True,
                'attempts': lock_record.get("count", 0),
                'unlock_time': lock_record["reset_time"]
            }
        
        return {
            'locked': False,
            'attempts': lock_record.get("count", 0) if lock_record else 0,
            'unlock_time': None
        }
    
    async def increment_otp_attempts(self, phone: str):
        """Increment failed OTP attempt counter"""
        current_time = datetime.utcnow()
        reset_time = current_time + timedelta(minutes=settings.rate_limit_lockout_min)
        
        lock_identifier = f"otp_lock:{phone}"
        await self.rate_limit_collection.update_one(
            {
                "identifier": lock_identifier,
                "reset_time": {"$gt": current_time}
            },
            {
                "$inc": {"count": 1},
                "$setOnInsert": {"reset_time": reset_time}
            },
            upsert=True
        )
    
    async def clear_otp_attempts(self, phone: str):
        """Clear failed OTP attempts after successful verification"""
        lock_identifier = f"otp_lock:{phone}"
        await self.rate_limit_collection.delete_many({
            "identifier": lock_identifier
        })
    
    async def generate_and_send_otp(self, phone: str, ip_address: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate OTP, send via SMS and store in database
        Returns: {'success': bool, 'message': str, 'otp_id': str, 'retry_after': int}
        """
        # Format phone number
        formatted_phone = sms_service.format_turkish_phone(phone)
        if not formatted_phone:
            return {
                'success': False,
                'message': 'Geçersiz telefon numarası formatı',
                'error_code': 'INVALID_PHONE'
            }
        
        # Check rate limits
        rate_limit_result = await self.check_rate_limit(formatted_phone, ip_address)
        if not rate_limit_result['allowed']:
            return {
                'success': False,
                'message': f"Rate limit aşıldı. {rate_limit_result['retry_after']} saniye sonra tekrar deneyin.",
                'retry_after': rate_limit_result['retry_after'],
                'error_code': 'RATE_LIMITED'
            }
        
        # Check OTP attempt lock
        attempt_check = await self.check_otp_attempts(formatted_phone)
        if attempt_check['locked']:
            unlock_minutes = (attempt_check['unlock_time'] - datetime.utcnow()).seconds // 60
            return {
                'success': False,
                'message': f'Çok fazla yanlış deneme. {unlock_minutes} dakika sonra tekrar deneyin.',
                'error_code': 'TOO_MANY_ATTEMPTS'
            }
        
        # Invalidate any existing OTPs for this phone
        await self.otp_collection.delete_many({"phone": formatted_phone})
        
        # Generate OTP
        otp_code = sms_service.generate_otp()
        otp_hash = sms_service.hash_otp(otp_code, formatted_phone)
        
        # Create OTP record
        current_time = datetime.utcnow()
        otp_record = {
            "phone": formatted_phone,
            "otp_hash": otp_hash,
            "created_at": current_time,
            "expires_at": current_time + timedelta(seconds=settings.otp_ttl_sec),
            "attempts": 0,
            "verified": False,
            "ip_address": ip_address,
            "device_id": device_id
        }
        
        # Insert OTP record
        result = await self.otp_collection.insert_one(otp_record)
        otp_id = str(result.inserted_id)
        
        # Send SMS
        sms_result = await sms_service.send_otp(formatted_phone, otp_code)
        
        if sms_result['success']:
            # Increment rate limits
            await self.increment_rate_limit(formatted_phone, ip_address)
            
            # Update OTP record with SMS details
            await self.otp_collection.update_one(
                {"_id": result.inserted_id},
                {
                    "$set": {
                        "sms_message_id": sms_result.get('message_id'),
                        "sms_provider": sms_result.get('provider'),
                        "sms_sent_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                'success': True,
                'message': 'OTP gönderildi',
                'otp_id': otp_id,
                'expires_in': settings.otp_ttl_sec,
                'formatted_phone': formatted_phone,
                'mock_otp': sms_service.get_mock_otp(formatted_phone) if settings.sms_mock_mode else None
            }
        else:
            # SMS sending failed, remove OTP record
            await self.otp_collection.delete_one({"_id": result.inserted_id})
            
            return {
                'success': False,
                'message': f'SMS gönderim hatası: {sms_result.get("error", "Bilinmeyen hata")}',
                'error_code': 'SMS_SEND_FAILED'
            }
    
    async def verify_otp(self, phone: str, otp_code: str, ip_address: str) -> Dict[str, Any]:
        """
        Verify OTP code
        Returns: {'success': bool, 'message': str, 'verified': bool}
        """
        # Format phone number
        formatted_phone = sms_service.format_turkish_phone(phone)
        if not formatted_phone:
            return {
                'success': False,
                'message': 'Geçersiz telefon numarası formatı',
                'error_code': 'INVALID_PHONE'
            }
        
        # Check OTP attempt lock
        attempt_check = await self.check_otp_attempts(formatted_phone)
        if attempt_check['locked']:
            unlock_minutes = (attempt_check['unlock_time'] - datetime.utcnow()).seconds // 60
            return {
                'success': False,
                'message': f'Çok fazla yanlış deneme. {unlock_minutes} dakika sonra tekrar deneyin.',
                'error_code': 'TOO_MANY_ATTEMPTS'
            }
        
        # Find active OTP
        current_time = datetime.utcnow()
        otp_record = await self.otp_collection.find_one({
            "phone": formatted_phone,
            "verified": False,
            "expires_at": {"$gt": current_time}
        })
        
        if not otp_record:
            return {
                'success': False,
                'message': 'OTP bulunamadı veya süresi dolmuş',
                'error_code': 'OTP_NOT_FOUND'
            }
        
        # Verify OTP
        if sms_service.verify_otp_hash(otp_code, formatted_phone, otp_record["otp_hash"]):
            # OTP is correct
            await self.otp_collection.update_one(
                {"_id": otp_record["_id"]},
                {
                    "$set": {
                        "verified": True,
                        "verified_at": current_time,
                        "verified_ip": ip_address
                    }
                }
            )
            
            # Clear failed attempts
            await self.clear_otp_attempts(formatted_phone)
            
            return {
                'success': True,
                'message': 'OTP doğrulandı',
                'verified': True,
                'otp_id': str(otp_record["_id"])
            }
        else:
            # OTP is incorrect
            await self.otp_collection.update_one(
                {"_id": otp_record["_id"]},
                {"$inc": {"attempts": 1}}
            )
            
            # Increment failed attempts
            await self.increment_otp_attempts(formatted_phone)
            
            return {
                'success': False,
                'message': 'Yanlış OTP kodu',
                'error_code': 'INVALID_OTP',
                'verified': False
            }
    
    async def cleanup_expired_otps(self):
        """Clean up expired OTP records (called periodically)"""
        current_time = datetime.utcnow()
        
        # Delete expired OTPs
        result = await self.otp_collection.delete_many({
            "expires_at": {"$lt": current_time}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} expired OTP records")
        
        # Delete expired rate limits
        rate_result = await self.rate_limit_collection.delete_many({
            "reset_time": {"$lt": current_time}
        })
        
        logger.info(f"Cleaned up {rate_result.deleted_count} expired rate limit records")