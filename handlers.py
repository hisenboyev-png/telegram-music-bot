import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from youtube import search_youtube, download_from_youtube, search_top_video_id
from instagram import download_from_instagram, download_instagram_video

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    user = update.effective_user
    # Salomlashish stikeri (agar muvaffaqiyatsiz bo'lsa, xatoni yutib yuboramiz)
    try:
        await update.message.reply_sticker("CAACAgIAAxkBAAEMD-ZmYgV_t5s_2b7x2gwh20wpc-J2AAICAA_d22A-g_NqgABu_AN4NAQ")
    except Exception as e:
        logger.warning("Start sticker yuborilmadi: %s", e)
    # Asosiy salomlashuv xabari har holda yuboriladi
    await update.message.reply_html(
        rf"👋 Salom, {user.mention_html()}! Men sizga YouTube va Instagram'dan musiqalarni topib beraman.",
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oddiy jonlilik testi: /ping -> pong"""
    await update.message.reply_text("pong")

async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Searches for songs and shows them as buttons or downloads directly from a link."""
    search_query = update.message.text
    logger.info(f"Search query: {search_query}")
    await update.message.reply_text("Qidirilmoqda...")

    try:
        if "instagram.com" in search_query:
            # Avval videoni yuboramiz va pastiga "Qo'shiqni yuklash" tugmasini joylaymiz
            try:
                video_path = await asyncio.wait_for(
                    asyncio.to_thread(download_instagram_video, search_query), timeout=60
                )
            except asyncio.TimeoutError:
                await update.message.reply_text("⏳ Instagram video yuklash juda uzoq cho'zildi. Keyinroq urinib ko'ring.")
                return

            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎵 Qo'shiqni yuklash", callback_data=f"ig_audio:{search_query}")]]
            )

            try:
                with open(video_path, 'rb') as vf:
                    await update.message.reply_video(video=vf, caption="Instagram video", reply_markup=keyboard)
            finally:
                try:
                    os.remove(video_path)
                except Exception:
                    pass
            return

        # YouTube URL bo'lsa — bevosita yuklaymiz
        if ("youtu.be" in search_query) or ("youtube.com" in search_query):
            try:
                new_filename = await asyncio.wait_for(
                    asyncio.to_thread(download_from_youtube, search_query), timeout=90
                )
            except asyncio.TimeoutError:
                await update.message.reply_text("⏳ YouTube yuklash juda uzoq cho'zildi. Keyinroq urinib ko'ring yoki boshqa havola yuboring.")
                return
            try:
                size_mb = os.path.getsize(new_filename) / (1024 * 1024)
                if size_mb > 49:
                    await update.message.reply_text("🚫 Fayl juda katta (>49MB). Qisqaroq trek tanlang yoki boshqa natijani sinab ko'ring.")
                    os.remove(new_filename)
                    return
            except Exception:
                pass
            with open(new_filename, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file)
            os.remove(new_filename)
            return

        # Matnli qidiruv: top natijani to'g'ridan-to'g'ri yuklaymiz
        try:
            video_id, title = await asyncio.wait_for(
                asyncio.to_thread(search_top_video_id, search_query), timeout=20
            )
        except asyncio.TimeoutError:
            video_id, title = None, None
        if video_id:
            if title:
                await update.message.reply_text(f"Topildi: {title}\nYuklanmoqda... ⏳")
            try:
                new_filename = await asyncio.wait_for(
                    asyncio.to_thread(download_from_youtube, video_id), timeout=90
                )
            except asyncio.TimeoutError:
                await update.message.reply_text("⏳ Yuklash juda uzoq cho'zildi. Keyinroq urinib ko'ring yoki boshqa natijani sinab ko'ring.")
                return
            try:
                size_mb = os.path.getsize(new_filename) / (1024 * 1024)
                if size_mb > 49:
                    await update.message.reply_text("🚫 Fayl juda katta (>49MB). Qisqaroq trek tanlang yoki boshqa natijani sinab ko'ring.")
                    os.remove(new_filename)
                    return
            except Exception:
                pass
            with open(new_filename, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file)
            os.remove(new_filename)
            return

        # Fallback: bir nechta variantlarni tugmalar bilan ko'rsatamiz
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(search_youtube, search_query), timeout=20
            )
        except asyncio.TimeoutError:
            results = []
        if results:
            keyboard = []
            for entry in results:
                button_text = f"🎵 {entry['title'][:50]}"
                callback_data = entry['id']
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Quyidagilardan birini tanlang:', reply_markup=reply_markup)
        else:
            await update.message.reply_sticker("CAACAgIAAxkBAAEMD-pmYgWb5gABiR3NB3Uf56n25Zl2qWwAAg4AA_d22A-AAAF0h2aJfrs0BA")
            await update.message.reply_text("😔 Kechirasiz, topilmadi yoki tarmoq sekin. Iltimos, YouTube havolasini yuboring yoki yana urinib ko'ring.")

    except Exception as e:
        logger.error(f"An error occurred in search_song: {e}", exc_info=True)
        await update.message.reply_sticker("CAACAgIAAxkBAAEMD-5mYgWvJgABHn5aTzRzFzTqo_mP5fMAAg8AA_d22A-g_NqgABu_AN4NAQ")
        await update.message.reply_text("🚫 Kechirasiz, qidirish paytida xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses to download the selected song."""
    query = update.callback_query
    await query.answer()
    video_id = query.data
    data = query.data
    
    # Edit caption if message is a media (video), otherwise edit text
    try:
        if getattr(query.message, 'video', None):
            await query.edit_message_caption(caption="Yuklanmoqda... ⏳")
        else:
            await query.edit_message_text(text="Yuklanmoqda... ⏳")
    except Exception:
        # If edit fails (e.g., no caption), ignore and proceed
        pass

    # Instagram audio callback: download and send quickly, then remove button
    if data.startswith("ig_audio:"):
        url = data.split(":", 1)[1]
        try:
            new_filename = await asyncio.to_thread(download_from_instagram, url)
            try:
                size_mb = os.path.getsize(new_filename) / (1024 * 1024)
                if size_mb > 49:
                    await query.edit_message_text(text="🚫 Fayl juda katta (>49MB). Qisqaroq trek tanlang yoki boshqa natijani sinab ko'ring.")
                    os.remove(new_filename)
                    return
            except Exception:
                pass
            with open(new_filename, 'rb') as audio_file:
                await context.bot.send_audio(chat_id=query.message.chat.id, audio=audio_file)
            os.remove(new_filename)
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"An error occurred in ig_audio callback: {e}", exc_info=True)
            await query.edit_message_text(text=f"🚫 Yuklashda xatolik yuz berdi: {e}")
        return

    try:
        # Offload heavy download to a background thread to keep bot responsive
        new_filename = await asyncio.to_thread(download_from_youtube, video_id)

        # If file is too large for Telegram (approx > 49MB), inform user
        try:
            size_mb = os.path.getsize(new_filename) / (1024 * 1024)
            if size_mb > 49:
                await query.edit_message_text(text="🚫 Fayl juda katta (>49MB). Iltimos, qisqaroq trek tanlang yoki boshqa natijani sinab ko'ring.")
                os.remove(new_filename)
                return
        except Exception:
            pass

        with open(new_filename, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=query.message.chat.id, audio=audio_file)
        os.remove(new_filename)
        await query.delete_message()

    except Exception as e:
        logger.error(f"An error occurred in button handler: {e}", exc_info=True)
        await query.edit_message_text(text=f"🚫 Yuklashda xatolik yuz berdi: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler to log exceptions for better observability."""
    try:
        logger.error("Unhandled exception: %s", context.error, exc_info=True)
        # Optional: we could notify admins here if ADMIN_CHAT_ID is set
    except Exception:
        pass