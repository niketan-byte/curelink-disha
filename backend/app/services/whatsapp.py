"""
WhatsApp Service - Handle outgoing messages via Meta Graph API
"""
import logging
import httpx
from typing import List, Optional, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Handle communication with WhatsApp Business Cloud API.
    """
    
    def __init__(self):
        # Force reload settings to pick up any env changes (crucial for temp tokens)
        from app.config import get_settings
        self.settings = get_settings()
        self.base_url = f"https://graph.facebook.com/v22.0/{self.settings.wa_phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.settings.wa_access_token}",
            "Content-Type": "application/json",
        }
        logger.info(f"WhatsApp Service initialized with Phone ID: {self.settings.wa_phone_number_id}")
        logger.info(f"Using Access Token prefix: {self.settings.wa_access_token[:15]}...")

    async def send_text_message(self, to: str, text: str):
        """Send a simple text message."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        return await self._send_request(payload)

    async def send_interactive_buttons(self, to: str, text: str, buttons: List[str]):
        """Send a message with interactive buttons (max 3)."""
        if not buttons:
            return await self.send_text_message(to, text)
            
        # WhatsApp supports max 3 buttons for quick replies
        buttons = buttons[:3]
        
        button_objs = []
        for i, btn_text in enumerate(buttons):
            button_objs.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": btn_text[:20]  # Max 20 chars
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {
                    "buttons": button_objs
                }
            }
        }
        return await self._send_request(payload)

    async def _send_request(self, payload: Dict[str, Any]):
        """Send request to Meta Graph API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"WhatsApp API error: {e}")
                logger.error(f"Response body: {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"WhatsApp API unexpected error: {e}")
                return None
