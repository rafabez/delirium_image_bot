import os
import asyncio
import logging
import urllib.parse
import ssl
import certifi
import requests
import random

from io import BytesIO
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip()
    if TELEGRAM_TOKEN.startswith("="):
        TELEGRAM_TOKEN = TELEGRAM_TOKEN[1:].strip()

if not TELEGRAM_TOKEN:
    raise EnvironmentError("O token do bot não foi configurado.")

SYSTEM_PROMPT = "Generate an image based on the prompt provided."

def call_pollinations_image(prompt: str, seed: int = None) -> bytes:
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        base_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        params = {
            "model": "flux",
            "nologo": "true",
            "width": "1024",
            "height": "1024",
            "referrer": "interzone.art.br"
        }
        if seed is not None:
            params["seed"] = str(seed)
        r = requests.get(base_url, params=params, timeout=60)
        r.raise_for_status()
        return r.content
    except requests.RequestException as e:
        logging.error("Pollinations Image API falhou: %s", e)
        return None

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return
    text = message.text.strip()
    chat = update.effective_chat
    
    # Handle group chats - check for bot mention
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        low = text.lower()
        if "@delirium" not in low:
            return
    
    # Generate random seed for image variation
    random_seed = random.randint(0, 2**32 - 1)
    
    # Notify user with delirium's edgy personality
    await message.reply_text("Generating the fucking image you requested, you lazy fuck...")
    
    loop = asyncio.get_running_loop()
    image_bytes = await loop.run_in_executor(None, call_pollinations_image, text, random_seed)
    
    if image_bytes is None:
        await message.reply_text("Failed to generate image. Please try again later.")
        return
    
    # Send the generated image
    image_stream = BytesIO(image_bytes)
    image_stream.name = "generated_image.png"
    await message.reply_photo(photo=image_stream)

def main():
    ssl.create_default_context(cafile=certifi.where())
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Delirium image bot está funcionando...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
