import asyncio
import os
import sys
import httpx

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings

async def fix_subscription():
    try:
        settings = get_settings()
        # Hardcoded from user's dashboard paste
        WABA_ID = "3573251329482953" 
        
        print(f"Checking subscriptions for WABA: {WABA_ID}...", flush=True)
        
        async with httpx.AsyncClient() as client:
            # 1. Check current subscriptions
            url = f"https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps"
            headers = {
                "Authorization": f"Bearer {settings.wa_access_token}",
                "Content-Type": "application/json",
            }
            
            response = await client.get(url, headers=headers)
            print(f"GET /subscribed_apps Status: {response.status_code}", flush=True)
            current_subs = response.json()
            print(f"Current Subscriptions: {current_subs}", flush=True)
            
            # 2. Force Subscribe (Overriding)
            print("Attempting to FORCE SUBSCRIBE...", flush=True)
            post_response = await client.post(url, headers=headers)
            print(f"POST /subscribed_apps Status: {post_response.status_code}", flush=True)
            print(f"Subscribe Response: {post_response.json()}", flush=True)
            
            if post_response.status_code == 200 and post_response.json().get('success'):
                print("SUCCESS: App subscribed to WABA webhooks.", flush=True)
            else:
                print("FAILURE: Could not subscribe.", flush=True)

    except Exception as e:
        print(f"Script Error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(fix_subscription())
