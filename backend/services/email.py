"""
Email service for Kuryecini
Supports console (dev) and SMTP (prod) providers
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Email service with multiple provider support"""
    
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "console")
        self.from_address = os.getenv("EMAIL_FROM", "no-reply@kuryecini.dev")
        
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        subject = "Kuryecini - Parola Sıfırlama"
        
        # Create reset link (will use frontend URL in production)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        body = f"""
Merhaba,

Kuryecini hesabınız için parola sıfırlama talebinde bulundunuz.

Parolanızı sıfırlamak için aşağıdaki bağlantıya tıklayın:
{reset_link}

Bu bağlantı 30 dakika içinde geçerliliğini yitirecektir.

Eğer bu talebi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.

Kuryecini Ekibi
        """
        
        return await self._send_email(to_email, subject, body, reset_token)
    
    async def _send_email(self, to_email: str, subject: str, body: str, token: Optional[str] = None) -> bool:
        """Send email using configured provider"""
        try:
            if self.provider == "console":
                return await self._send_console_email(to_email, subject, body, token)
            elif self.provider == "smtp":
                return await self._send_smtp_email(to_email, subject, body)
            else:
                logger.error(f"Unknown email provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def _send_console_email(self, to_email: str, subject: str, body: str, token: Optional[str] = None) -> bool:
        """Console email provider for development"""
        print("\n" + "="*60)
        print("📧 EMAIL (CONSOLE MODE)")
        print("="*60)
        print(f"From: {self.from_address}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Time: {datetime.now().isoformat()}")
        if token:
            print(f"Reset Token: {token}")
        print("-"*60)
        print(body)
        print("="*60)
        
        logger.info(f"Console email sent to {to_email} - Token: {token}")
        return True
    
    async def _send_smtp_email(self, to_email: str, subject: str, body: str) -> bool:
        """SMTP email provider for production (placeholder)"""
        # TODO: Implement SMTP/Resend integration for production
        logger.info(f"SMTP email would be sent to {to_email}")
        return True

# Global email service instance
email_service = EmailService()