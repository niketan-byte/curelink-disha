import asyncio
import os
import sys
import httpx

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings

async def send_outbound():
    try:
        settings = get_settings()
        print(f"Testing outbound to user...", flush=True)
        print(f"Phone ID: {settings.wa_phone_number_id}", flush=True)
        
        # dynamic recipient
        RECIPIENT_NUMBER = "919039456792" 
        
        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/v22.0/{settings.wa_phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {settings.wa_access_token}",
                "Content-Type": "application/json",
            }
            
            # Try sending a standard hello_world template which is usually available
            payload = {
                "messaging_product": "whatsapp",
                "to": RECIPIENT_NUMBER,
                "type": "template",
                "template": {
                    "name": "hello_world",
                    "language": {
                        "code": "en_US"
                    }
                }
            }
            
            print(f"Sending payload to {RECIPIENT_NUMBER}...", flush=True)
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"Status Code: {response.status_code}", flush=True)
            if response.status_code != 200:
                print(f"Error Response: {response.text}", flush=True)
            else:
                print(f"Success! Response: {response.json()}", flush=True)

    except Exception as e:
        print(f"Script Error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(send_outbound())
