import logging
import os
import asyncio
import hashlib
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from youtube import search_youtube, download_from_youtube, search_top_video_id
from instagram import download_from_instagram, download_instagram_video

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# In-memory map for short Instagram audio tokens -> original URL
IG_AUDIO_MAP: dict[str, dict] = {}

def _prune_ig_audio_map(max_age: int = 600, max_size: int = 500) -> None:
    """Prune expired or excessive callback entries to keep memory bounded."""
    now = time.time()
    # Remove old entries
    for k, v in list(IG_AUDIO_MAP.items()):
        if now - v.get("ts", now) > max_age:
            IG_AUDIO_MAP.pop(k, None)
    # Bound size
    if len(IG_AUDIO_MAP) > max_size:
        items = sorted(IG_AUDIO_MAP.items(), key=lambda kv: kv[1].get("ts", 0))
        for k, _ in items[: len(IG_AUDIO_MAP) - max_size]:
            IG_AUDIO_MAP.pop(k, None)

def _store_ig_audio_url(url: str) -> str:
    """Store URL and return a short token for Telegram callback_data (<=64 bytes)."""
    token = hashlib.sha256(url.encode()).hexdigest()[:32]
    IG_AUDIO_MAP[token] = {"url": url, "ts": time.time()}
    _prune_ig_audio_map()
    return token

def _get_ig_audio_url(token: str) -> str | None:
    """Retrieve original Instagram URL for a given token."""
    entry = IG_AUDIO_MAP.get(token)
    return entry["url"] if entry else None

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
            # Tezlik uchun parallel: video (≤25s) va audio (≤45s) yuklashni birga boshlaymiz
            token = _store_ig_audio_url(search_query)
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎵 Qo'shiqni yuklash", callback_data=f"ig_audio:{token}")]]
            )

            video_task = asyncio.create_task(
                asyncio.wait_for(asyncio.to_thread(download_instagram_video, search_query), timeout=25)
            )
            audio_task = asyncio.create_task(
                asyncio.wait_for(asyncio.to_thread(download_from_instagram, search_query), timeout=45)
            )

            done, pending = await asyncio.wait({video_task, audio_task}, return_when=asyncio.FIRST_COMPLETED)
            # Agar video tayyor bo'lsa — videoni tugma bilan yuboramiz; aks holda — audio yuboramiz
            if video_task in done and not video_task.cancelled():
                try:
                    video_path = video_task.result()
                    try:
                        with open(video_path, 'rb') as vf:
                            await update.message.reply_video(video=vf, caption="Instagram video", reply_markup=keyboard)
                    finally:
                        try:
                            os.remove(video_path)
                        except Exception:
                            pass
                except Exception:
                    # Video muvaffaqiyatsiz bo'lsa, audio natijasini tekshiramiz
                    pass
            elif audio_task in done and not audio_task.cancelled():
                try:
                    new_filename = audio_task.result()
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
                    # Agar keyin video tayyor bo'lsa, alohida yuborib qo'yamiz
                    try:
                        video_path = await video_task
                        try:
                            with open(video_path, 'rb') as vf:
                                await update.message.reply_video(video=vf, caption="Instagram video", reply_markup=keyboard)
                        finally:
                            try:
                                os.remove(video_path)
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    # Audio ham muvaffaqiyatsiz bo'lsa, foydalanuvchiga xabar beramiz
                    await update.message.reply_text("😔 Kechirasiz, Instagram linkdan audio/video olinmadi. Keyinroq urinib ko'ring.")
                return

            # Agar hech biri 25–45s ichida tugamasa — foydalanuvchiga xabar beramiz
            for t in pending:
                t.cancel()
            await update.message.reply_text("⏳ Juda sekin tarmoq. Audio/video yuklashni keyinroq qayta urinib ko'ring.")
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
            try:
                await update.message.reply_sticker("CAACAgIAAxkBAAEMD-pmYgWb5gABiR3NB3Uf56n25Zl2qWwAAg4AA_d22A-AAAF0h2aJfrs0BA")
            except Exception:
                pass
            await update.message.reply_text("😔 Kechirasiz, topilmadi yoki tarmoq sekin. Iltimos, YouTube havolasini yuboring yoki yana urinib ko'ring.")

    except Exception as e:
        logger.error(f"An error occurred in search_song: {e}", exc_info=True)
        try:
            await update.message.reply_sticker("CAACAgIAAxkBAAEMD-5mYgWvJgABHn5aTzRzFzTqo_mP5fMAAg8AA_d22A-g_NqgABu_AN4NAQ")
        except Exception:
            pass
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
        token = data.split(":", 1)[1]
        url = _get_ig_audio_url(token)
        if not url:
            await query.edit_message_text(text="⏳ Tugma muddati tugagan. Iltimos, linkni qayta yuboring.")
            return
        try:
            new_filename = await asyncio.wait_for(
                asyncio.to_thread(download_from_instagram, url), timeout=45
            )
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
        except asyncio.TimeoutError:
            try:
                if getattr(query.message, 'video', None):
                    await query.edit_message_caption(caption="⏳ Audio yuklash juda uzoq cho'zildi. Keyinroq qayta urinib ko'ring.")
                else:
                    await query.edit_message_text(text="⏳ Audio yuklash juda uzoq cho'zildi. Keyinroq qayta urinib ko'ring.")
            except Exception:
                pass
            return
        except Exception as e:
            logger.error(f"An error occurred in ig_audio callback: {e}", exc_info=True)
            await query.edit_message_text(text=f"🚫 Yuklashda xatolik yuz berdi: {e}")
        return

    try:
        # Offload heavy download to a background thread to keep bot responsive
        new_filename = await asyncio.wait_for(
            asyncio.to_thread(download_from_youtube, video_id), timeout=90
        )

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