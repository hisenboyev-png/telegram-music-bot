import logging
import os
import requests
from telegram.error import Conflict
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers import start, search_song, button, error_handler

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
    # Try deleting webhook to avoid mixed modes
    try:
        resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
        if resp.ok:
            logger.info("Webhook o‘chirildi yoki mavjud emas edi (OK).")
        else:
            logger.warning("Webhook o‘chirishda muammo: %s", resp.text)
    except Exception as e:
        logger.warning("Webhook o‘chirib bo‘lmadi: %s", e)

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_song))
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(error_handler)
    logger.info("Bot ishga tushmoqda (polling, drop_pending_updates=True)...")
    try:
        application.run_polling(drop_pending_updates=True)
    except Conflict as e:
        logger.error(
            "Polling CONFLICT: boshqa instansiya getUpdates chaqiryapti. Iltimos, faqat bitta instansiyani qoldiring. Xato: %s",
            e,
        )
        raise SystemExit(1)

if __name__ == "__main__":
    main()