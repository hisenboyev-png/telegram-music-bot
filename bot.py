import logging
import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Read token from environment for deployment safety
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    await update.message.reply_text("Salom! Men sizning musiqiy botingizman. Menga qo'shiq nomini yuboring, men uni topib beraman.")

async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Searches for a song on YouTube and sends it to the user."""
    search_query = update.message.text
    logger.info(f"Search query: {search_query}")
    await update.message.reply_text("Qidirilmoqda...")
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        logger.info(f"yt-dlp options: {ydl_opts}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)
            logger.info(f"Extracted info: {info}")
            
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
                filename = ydl.prepare_filename(video_info)
                logger.info(f"Original filename: {filename}")
                base, ext = os.path.splitext(filename)
                new_filename = base + '.mp3'
                logger.info(f"New filename: {new_filename}")
                
                # Send the audio file
                with open(new_filename, 'rb') as audio_file:
                    await update.message.reply_audio(audio=audio_file)
                
                # Clean up the file
                os.remove(new_filename)
            else:
                await update.message.reply_text("Kechirasiz, ushbu nom bilan qo'shiq topilmadi. Boshqa nom bilan urinib ko'ring.")

    except Exception as e:
        logger.error(f"An error occurred in search_song: {e}", exc_info=True)
        await update.message.reply_text("Kechirasiz, qo'shiqni topa olmadim. Boshqa nom bilan urinib ko'ring.")

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable is not set.")
        raise SystemExit("BOT_TOKEN environment variable is not set.")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_song))

    application.run_polling()

if __name__ == "__main__":
    main()