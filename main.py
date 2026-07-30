import os
import io
import logging
import asyncio
from datetime import datetime
from PIL import Image
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token from environment variable
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in environment variables!")

# API Keys (optional, for better image generation)
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")

# User session data
user_data = {}

# ==================== UTILITY FUNCTIONS ====================

async def shorten_url(url: str) -> str:
    """Shorten URL using TinyURL API (free, no API key needed)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://tinyurl.com/api-create.php?url={url}") as resp:
                if resp.status == 200:
                    short_url = await resp.text()
                    return short_url.strip()
                return url
    except:
        return url

async def generate_image(prompt: str) -> bytes:
    """Generate image using HuggingFace API (free tier)"""
    if not HUGGINGFACE_API_KEY:
        # Fallback: return a placeholder image
        return None
    
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json={"inputs": prompt}) as resp:
                if resp.status == 200:
                    return await resp.read()
                return None
    except:
        return None

async def convert_image(image_data: bytes, target_format: str) -> bytes:
    """Convert image to different format"""
    try:
        img = Image.open(io.BytesIO(image_data))
        output = io.BytesIO()
        
        # Handle different formats
        format_map = {
            "png": "PNG",
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "webp": "WEBP",
            "bmp": "BMP"
        }
        
        img_format = format_map.get(target_format.lower(), "PNG")
        
        # Convert RGBA to RGB for JPEG
        if img_format == "JPEG" and img.mode == "RGBA":
            img = img.convert("RGB")
            
        img.save(output, format=img_format)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Image conversion error: {e}")
        return None

# ==================== BOT COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with main menu"""
    keyboard = [
        [InlineKeyboardButton("🖼️ Image Converter", callback_data="convert")],
        [InlineKeyboardButton("🎨 Image Generator", callback_data="generate")],
        [InlineKeyboardButton("🔗 URL Shortener", callback_data="shorten")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎉 Welcome to Snap5Bot!\n\n"
        f"I can help you with:\n"
        f"🖼️ Convert images to different formats\n"
        f"🎨 Generate images from text (AI)\n"
        f"🔗 Shorten long URLs\n\n"
        f"Select an option below to get started!"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message"""
    help_text = (
        "📖 *Snap5Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Show main menu\n"
        "/help - Show this help\n"
        "/convert - Convert an image\n"
        "/generate - Generate an image from text\n"
        "/shorten - Shorten a URL\n\n"
        "*Image Converter:*\n"
        "Send me an image and choose a format (PNG, JPG, WEBP, BMP)\n\n"
        "*Image Generator:*\n"
        "Type: /generate [your prompt]\n"
        "Example: /generate a cat riding a bicycle\n\n"
        "*URL Shortener:*\n"
        "Type: /shorten [your URL]\n"
        "Example: /shorten https://example.com/very-long-url\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "convert":
        await query.edit_message_text(
            "🖼️ *Image Converter*\n\n"
            "Send me an image, then choose the format you want to convert it to.\n\n"
            "Supported formats: PNG, JPG, WEBP, BMP",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = 'convert'
        
    elif action == "generate":
        await query.edit_message_text(
            "🎨 *Image Generator*\n\n"
            "Send me a text description of the image you want to create.\n\n"
            "Example: *a beautiful sunset over mountains*",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = 'generate'
        
    elif action == "shorten":
        await query.edit_message_text(
            "🔗 *URL Shortener*\n\n"
            "Send me a URL to shorten.\n\n"
            "Example: `https://example.com/very-long-url`",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = 'shorten'
        
    elif action == "about":
        await query.edit_message_text(
            "ℹ️ *About Snap5Bot*\n\n"
            "🤖 Snap5Bot is a multipurpose Telegram bot with:\n"
            "• Image Converter (PNG, JPG, WEBP, BMP)\n"
            "• AI Image Generator (via HuggingFace)\n"
            "• URL Shortener (via TinyURL)\n\n"
            "💡 Created by @YourUsername\n"
            "📅 Version 1.0.0",
            parse_mode="Markdown"
        )
        
    elif action.startswith("format_"):
        target_format = action.replace("format_", "")
        image_data = context.user_data.get('image_to_convert')
        
        if not image_data:
            await query.edit_message_text("❌ No image found. Please send an image first.")
            return
        
        await query.edit_message_text(f"⏳ Converting to {target_format.upper()}...")
        
        converted = await convert_image(image_data, target_format)
        if converted:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=io.BytesIO(converted),
                filename=f"converted.{target_format.lower()}",
                caption=f"✅ Converted to {target_format.upper()}!"
            )
        else:
            await query.edit_message_text("❌ Failed to convert image. Please try again.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages based on current mode"""
    user_id = update.effective_user.id
    text = update.message.text
    mode = context.user_data.get('mode', '')
    
    # ===== IMAGE GENERATOR =====
    if mode == 'generate' or (text and text.startswith('/generate')):
        # Extract prompt
        if text.startswith('/generate'):
            prompt = text.replace('/generate', '').strip()
        else:
            prompt = text
        
        if not prompt:
            await update.message.reply_text("❌ Please provide a description.\nExample: `/generate a cat`")
            return
        
        await update.message.reply_text(f"🎨 Generating image for: *{prompt}*...\n⏳ This may take up to 30 seconds.", parse_mode="Markdown")
        
        image_bytes = await generate_image(prompt)
        if image_bytes:
            await update.message.reply_photo(
                photo=io.BytesIO(image_bytes),
                caption=f"✅ Generated image for: *{prompt}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Failed to generate image. Please try again later.\n"
                "💡 Tip: Try a simpler description."
            )
        context.user_data['mode'] = ''
        return
    
    # ===== URL SHORTENER =====
    if mode == 'shorten' or text.startswith('/shorten'):
        url = text.replace('/shorten', '').strip() if text.startswith('/shorten') else text
        
        if not url or not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Please provide a valid URL starting with http:// or https://")
            return
        
        await update.message.reply_text(f"🔗 Shortening URL...")
        short = await shorten_url(url)
        await update.message.reply_text(f"✅ *Shortened URL:*\n{short}", parse_mode="Markdown")
        context.user_data['mode'] = ''
        return
    
    # ===== IMAGE CONVERTER =====
    if mode == 'convert':
        # Check if message has image
        if not update.message.photo and not update.message.document:
            await update.message.reply_text(
                "❌ Please send an image (photo or document).\n\n"
                "Or type /cancel to exit."
            )
            return
        
        # Get image
        photo = update.message.photo[-1] if update.message.photo else None
        if not photo:
            # Handle document
            document = update.message.document
            if document.mime_type and document.mime_type.startswith('image/'):
                file_id = document.file_id
            else:
                await update.message.reply_text("❌ Please send a valid image file.")
                return
        else:
            file_id = photo.file_id
            
        # Download image
        file = await context.bot.get_file(file_id)
        image_bytes = await file.download_as_bytearray()
        
        context.user_data['image_to_convert'] = bytes(image_bytes)
        
        # Show format options
        keyboard = [
            [InlineKeyboardButton("📷 PNG", callback_data="format_png")],
            [InlineKeyboardButton("🖼️ JPG", callback_data="format_jpg")],
            [InlineKeyboardButton("🌐 WEBP", callback_data="format_webp")],
            [InlineKeyboardButton("🖼️ BMP", callback_data="format_bmp")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🖼️ Choose the format to convert your image to:",
            reply_markup=reply_markup
        )
        return
    
    # ===== DEFAULT =====
    await update.message.reply_text(
        "🤔 I didn't understand that.\n"
        "Use /start to see the main menu or /help for assistance."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text("✅ Cancelled. Use /start to begin again.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Something went wrong. Please try again later."
        )

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("generate", handle_message))
    application.add_handler(CommandHandler("shorten", handle_message))
    
    # Add callback and message handlers
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot with polling
    logger.info("Starting Snap5Bot with long polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
