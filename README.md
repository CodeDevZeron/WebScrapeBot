# Telegram Web Cloner Bot (By DevZeron)

## Features
- Host on Vercel (Webhook + FastAPI)
- /clone <url> → Clone website (HTML, CSS, JS, images) → Zip
- Dynamic loading message (edit + auto refresh after limit)
- Error handling + Success file delivery

## Deploy
1. Upload project to Vercel
2. No need to set env vars (already in index.py, but better use env)
3. Deploy
4. Set Telegram webhook:
   ```bash
   curl -F "url=https://webscrapebot.vercel.app/webhook" https://api.telegram.org/bot8472822689:AAF5YmlrLD9bPCtNSk0TDhVcVzvK1l2mBdk/setWebhook
