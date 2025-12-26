"""
WhatsApp Webhook Routes
"""
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from app.config import get_settings
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/whatsapp", tags=["WhatsApp"])

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    WhatsApp Webhook Verification (GET).
    Used by Meta to verify the server when setting up the webhook.
    """
    settings = get_settings()
    
    if hub_mode == "subscribe" and hub_verify_token == settings.wa_verify_token:
        logger.info("WhatsApp Webhook verified successfully!")
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning("WhatsApp Webhook verification failed.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("")
async def handle_whatsapp_message(request: Request):
    """
    Handle incoming WhatsApp messages (POST).
    """
    body = await request.json()
    logger.info(f"Received WhatsApp webhook: {body}")

    # Standard WhatsApp Cloud API message structure
    try:
        if not body.get("entry"):
            return {"status": "ignored"}
            
        for entry in body["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if not value.get("messages"):
                    continue
                    
                for message in value["messages"]:
                    wa_id = message.get("from")
                    message_type = message.get("type")
                    
                    text = ""
                    if message_type == "text":
                        text = message["text"].get("body", "")
                    elif message_type == "interactive":
                        # Handle button replies
                        interactive = message.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            text = interactive["button_reply"].get("title", "")
                    
                    if not wa_id or not text:
                        continue
                        
                    # Process via Orchestrator
                    orchestrator = ChatOrchestrator()
                    user_msg, assistant_msg = await orchestrator.process_message(
                        user_id=wa_id,
                        content=text
                    )
                    
                    # Send response back to WhatsApp
                    wa_service = WhatsAppService()
                    if assistant_msg.options:
                        await wa_service.send_interactive_buttons(
                            to=wa_id,
                            text=assistant_msg.content,
                            buttons=assistant_msg.options
                        )
                    else:
                        await wa_service.send_text_message(
                            to=wa_id,
                            text=assistant_msg.content
                        )
                        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        # Always return 200 to WhatsApp to avoid retries on failure during development
        return {"status": "error", "detail": str(e)}
