import os

import httpx

telegram_token = os.getenv("TELEGRAM_TOKEN")
bot_url = input("Please enter bot url: ")
set_webhook_url = (
    f"http://api.telegram.org/bot{telegram_token}/setWebhook?url={bot_url}"
)
r = httpx.get(set_webhook_url)

if r.json()["ok"]:
    print("Webhook configured!")
else:
    print("Error, this is telegram's response")
    print(r.json())
