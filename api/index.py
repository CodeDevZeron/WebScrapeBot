import os
import requests
import asyncio
from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse
from bs4 import BeautifulSoup
from telegram import Update, Bot
from urllib.parse import urljoin, urlparse
import zipfile
import io

# ---------- CONFIG ----------
BOT_TOKEN = "8472822689:AAF5YmlrLD9bPCtNSk0TDhVcVzvK1l2mBdk"
APP_URL = "https://webscrapebot.vercel.app"
# ----------------------------

bot = Bot(BOT_TOKEN)
app = FastAPI()

# -------------------- Website Clone Function --------------------
def clone_website(url: str):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    folder_name = domain.split(".")[0]
    zip_buffer = io.BytesIO()

    visited = set()
    assets = []

    def fetch_file(file_url, path):
        if file_url in visited:
            return
        visited.add(file_url)
        try:
            r = requests.get(file_url, timeout=10)
            if r.status_code == 200:
                assets.append((path, r.content))
        except:
            pass

    # Main page
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # Save index.html
    assets.append((f"{folder_name}/index.html", r.text.encode()))

    # Collect assets
    for tag in soup.find_all(["link", "script", "img"]):
        attr = "href" if tag.name == "link" else "src"
        link = tag.get(attr)
        if link:
            file_url = urljoin(url, link)
            path = f"{folder_name}/{link.lstrip('/')}"
            fetch_file(file_url, path)

    # Build ZIP
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for path, data in assets:
            zipf.writestr(path, data)

    zip_buffer.seek(0)
    return zip_buffer, f"{folder_name}_By_DevZeron.zip"

@app.get("/api/clone")
def clone(url: str = Query(...)):
    zip_buffer, filename = clone_website(url)
    return FileResponse(zip_buffer, media_type="application/zip", filename=filename)

# -------------------- Telegram Webhook Handler --------------------
loading_frames = ["⏳ Loading.", "⏳ Loading..", "⏳ Loading..."]

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)

    if update.message and update.message.text:
        text = update.message.text.strip()
        chat_id = update.message.chat_id

        if text.startswith("/start"):
            await bot.send_message(chat_id, "👋 Send /clone <website_url> to clone a site!")
        
        elif text.startswith("/clone"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await bot.send_message(chat_id, "⚠️ Usage: /clone https://example.com")
                return {"ok": True}
            
            url = parts[1]
            msg = await bot.send_message(chat_id, "⏳ Loading.")  # first message
            message_id = msg.message_id
            edits = 0
            i = 0

            async def loading_anim():
                nonlocal message_id, edits, i
                try:
                    while True:
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=loading_frames[i % len(loading_frames)]
                        )
                        await asyncio.sleep(1.5)
                        i += 1
                        edits += 1
                        if edits >= 190:  # edit limit
                            await bot.delete_message(chat_id, message_id)
                            new_msg = await bot.send_message(chat_id, "⏳ Loading.")
                            message_id = new_msg.message_id
                            edits = 0
                except:
                    pass

            task = asyncio.create_task(loading_anim())

            try:
                r = requests.get(f"{APP_URL}/api/clone", params={"url": url}, stream=True, timeout=60)
                task.cancel()

                if r.status_code == 200:
                    filename = r.headers.get("content-disposition", "clone.zip").split("filename=")[-1]
                    await bot.delete_message(chat_id, message_id)
                    await bot.send_document(chat_id, document=r.content, filename=filename, caption="✅ Clone Success!")
                else:
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="❌ Failed to clone site.")
            except Exception as e:
                task.cancel()
                try:
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"⚠️ Error: {e}")
                except:
                    await bot.send_message(chat_id, f"⚠️ Error: {e}")

    return {"ok": True}
