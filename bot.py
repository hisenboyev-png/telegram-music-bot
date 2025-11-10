import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import asyncio
from handlers import start, search_song, button

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Read token from environment for deployment safety
TOKEN = os.environ.get("BOT_TOKEN")

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable is not set.")
        raise SystemExit("BOT_TOKEN environment variable is not set.")
    application = Application.builder().token(TOKEN).build()

    # Agar webhook avval o'rnatilgan bo'lsa, polling bilan konflikt bo'lmasligi uchun uni o'chirib tashlaymiz
    try:
        asyncio.get_event_loop().run_until_complete(
            application.bot.delete_webhook(drop_pending_updates=True)
        )
        logger.info("Webhook o'chirildi, polling rejimi yoqildi.")
    except Exception as e:
        logger.warning(f"Webhookni o'chirishda muammo: {e}")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_song))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == "__main__":
    main()