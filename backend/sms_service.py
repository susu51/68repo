import hashlib
import hmac
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
import pyotp
import phonenumbers
from phonenumbers import NumberParseException
from config import settings

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service for OTP delivery with Netgsm integration and mock support"""
    
    def __init__(self):
        self.netgsm_url = "https://api.netgsm.com.tr/sms/send/get"
        self.mock_otps: Dict[str, str] = {}  # For development mock
        
    def format_turkish_phone(self, phone: str) -> Optional[str]:
        """
        Format Turkish phone number to international format
        Supports: +90xxxxxxxxxx, 90xxxxxxxxxx, 0xxxxxxxxxx, 5xxxxxxxxx
        Returns: +90xxxxxxxxxx format or None if invalid
        """
        try:
            # Clean the number
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            # Handle different Turkish phone formats
            if clean_phone.startswith('90') and len(clean_phone) == 12:
                # Already in 90xxxxxxxxxx format
                formatted = '+' + clean_phone
            elif clean_phone.startswith('0') and len(clean_phone) == 11:
                # 0xxxxxxxxxx format, remove 0 and add +90
                formatted = '+90' + clean_phone[1:]
            elif clean_phone.startswith('5') and len(clean_phone) == 10:
                # 5xxxxxxxxx format, add +90
                formatted = '+90' + clean_phone
            elif phone.startswith('+90') and len(clean_phone) == 12:
                # +90xxxxxxxxxx format already
                formatted = phone
            else:
                return None
                
            # Validate using phonenumbers library
            parsed_number = phonenumbers.parse(formatted, 'TR')
            if phonenumbers.is_valid_number(parsed_number):
                return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            else:
                return None
                
        except (NumberParseException, ValueError):
            return None
    
    def generate_otp(self) -> str:
        """Generate 6-digit OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(settings.otp_length)])
    
    def hash_otp(self, otp: str, phone: str) -> str:
        """Hash OTP with phone number as salt for secure storage"""
        salt = phone.encode('utf-8')
        return hmac.new(salt, otp.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def verify_otp_hash(self, otp: str, phone: str, hashed_otp: str) -> bool:
        """Verify OTP against stored hash"""
        computed_hash = self.hash_otp(otp, phone)
        return hmac.compare_digest(computed_hash, hashed_otp)
    
    async def send_sms_netgsm(self, phone: str, message: str) -> Dict[str, Any]:
        """Send SMS via Netgsm API"""
        if not settings.netgsm_user or not settings.netgsm_pass:
            raise ValueError("Netgsm credentials not configured")
            
        params = {
            'usercode': settings.netgsm_user,
            'password': settings.netgsm_pass,
            'gsmno': phone.replace('+', ''),  # Remove + for Netgsm
            'message': message,
            'msgheader': settings.netgsm_header,
            'filter': '0',  # No filter
            'startdate': '',
            'stopdate': '',
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.netgsm_url, params=params, timeout=10) as response:
                    response_text = await response.text()
                    
                    # Netgsm returns different response codes
                    if response_text.startswith('00 '):
                        # Success, extract message ID
                        message_id = response_text.split(' ')[1] if ' ' in response_text else None
                        return {
                            'success': True,
                            'message_id': message_id,
                            'provider': 'netgsm',
                            'response': response_text
                        }
                    else:
                        # Error occurred
                        error_codes = {
                            '20': 'Message too long',
                            '30': 'Invalid username/password',
                            '40': 'Invalid message header',
                            '50': 'Invalid phone number',
                            '60': 'Invalid message',
                            '70': 'Insufficient credits'
                        }
                        error_msg = error_codes.get(response_text, f'Unknown error: {response_text}')
                        return {
                            'success': False,
                            'error': error_msg,
                            'provider': 'netgsm',
                            'response': response_text
                        }
                        
        except Exception as e:
            logger.error(f"Netgsm SMS send error: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'provider': 'netgsm'
            }
    
    async def send_sms_mock(self, phone: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending for development"""
        # Extract OTP from message (assuming format contains 6 digits)
        import re
        otp_match = re.search(r'\b\d{6}\b', message)
        if otp_match:
            otp = otp_match.group()
            self.mock_otps[phone] = otp
            logger.info(f"MOCK SMS - Phone: {phone}, OTP: {otp}, Message: {message}")
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        return {
            'success': True,
            'message_id': f'mock_{int(time.time())}_{random.randint(1000, 9999)}',
            'provider': 'mock',
            'response': 'Mock SMS sent successfully'
        }
    
    def get_mock_otp(self, phone: str) -> Optional[str]:
        """Get mock OTP for development (only in mock mode)"""
        if settings.sms_mock_mode:
            return self.mock_otps.get(phone)
        return None
    
    def format_otp_message(self, otp: str) -> str:
        """Format OTP message according to specification"""
        return f"DeliverTR OTP: {otp}. 2 dk içinde kullanın. Paylaşmayın."
    
    async def send_otp(self, phone: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP via SMS (uses mock or real SMS based on configuration)
        """
        # Format phone number
        formatted_phone = self.format_turkish_phone(phone)
        if not formatted_phone:
            return {
                'success': False,
                'error': 'Invalid phone number format'
            }
        
        # Format message
        message = self.format_otp_message(otp)
        
        # Send via appropriate method
        if settings.sms_mock_mode:
            result = await self.send_sms_mock(formatted_phone, message)
        else:
            result = await self.send_sms_netgsm(formatted_phone, message)
        
        # Add phone formatting info to result
        result['formatted_phone'] = formatted_phone
        result['original_phone'] = phone
        
        return result

# Global SMS service instance
sms_service = SMSService()

# Add missing import
import asyncio