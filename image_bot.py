import os
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import ssl
import certifi
from io import BytesIO

# Load TELEGRAM_TOKEN from environment variables (set this in your hosting platform)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise EnvironmentError("TELEGRAM_TOKEN not set! Please configure it in your environment variables.")

# Optional system prompt (not used by the image API)
SYSTEM_PROMPT = "Generate an image based on the prompt provided."

def call_pollinations_image_api(prompt: str) -> bytes:
    """
    Calls the Pollinations.AI Image Generation API to generate an image based on the provided prompt.
    Uses the 'turbo' model and sets nologo=true.
    
    Parameters:
        prompt (str): A text description of the desired image.
        
    Returns:
        bytes: The image data (PNG/JPEG) if successful; otherwise, None.
    """
    try:
        base_url = "https://image.pollinations.ai/prompt/"
        # URL-encode the prompt
        encoded_prompt = requests.utils.quote(prompt)
        params = {
            "model": "flux",
            "nologo": "true",
            "width": "1024",
            "height": "1024"
        }
        # Compose the full URL and make the GET request
        response = requests.get(f"{base_url}{encoded_prompt}", params=params)
        response.raise_for_status()
        return response.content
    except requests.RequestException:
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming messages by using the message text as an image prompt.
    Calls the Pollinations.AI API and sends back the generated image.
    """
    # Check if the bot is mentioned explicitly by username (@delirium)
    bot_username = "delirium"  # Replace with the actual bot username if different
    user_prompt = update.message.text.strip()

    if f"@{bot_username}" not in user_prompt:
        return  # Do nothing if the bot is not mentioned
    
    # Notify the user that image generation is underway.
    await update.message.reply_text("Generating the fucking image you requested, you lazy fuck...")

    loop = asyncio.get_running_loop()
    image_bytes = await loop.run_in_executor(None, call_pollinations_image_api, user_prompt)

    if image_bytes is None:
        await update.message.reply_text("Failed to generate image. Please try again later.")
        return

    # Wrap the returned bytes in a BytesIO object so Telegram can send it as a photo.
    image_stream = BytesIO(image_bytes)
    image_stream.name = "generated_image.png"
    await update.message.reply_photo(photo=image_stream)

def main():
    """
    Configures and starts the Telegram image generation bot.
    """
    # Build the Telegram application directly using ApplicationBuilder
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add a handler for all non-command text messages.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Image generation bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
