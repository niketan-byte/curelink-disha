import asyncio
print("STARTING TEST SCRIPT", flush=True)
import os
import sys
import httpx
print("Imports done", flush=True)

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
print("Path added", flush=True)

from app.config import get_settings
print("Config imported", flush=True)

async def test_whatsapp():
    try:
        settings = get_settings()
        print(f"Testing with Phone ID: {settings.wa_phone_number_id}", flush=True)
        print(f"Token: {settings.wa_access_token[:10]}...", flush=True)
        
        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/v21.0/{settings.wa_phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {settings.wa_access_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": "919039456792", # User's verified number
                "type": "text",
                "text": {"body": "Test verification message from Curelink Bot"}
            }
            
            print(f"Sending to URL: {url}", flush=True)
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status Code: {response.status_code}", flush=True)
            print(f"Response Body: {response.text}", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_whatsapp())
