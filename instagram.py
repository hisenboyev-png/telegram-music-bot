import yt_dlp
import os

def _ensure_download_dir(path: str = "downloads") -> str:
    if not os.path.isdir(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            return ""
    return path

def download_from_instagram(url):
    """Download audio from Instagram-compatible URLs without ffmpeg postprocessing.
    Prefer m4a/opus directly and return the file path.
    """
    downloads_dir = _ensure_download_dir("downloads")
    outtmpl = '%(id)s.%(ext)s'
    if downloads_dir:
        outtmpl = os.path.join(downloads_dir, outtmpl)

    ydl_opts = {
        'format': 'bestaudio[acodec~=^mp4a]/bestaudio[ext=m4a]/bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': outtmpl,
        'socket_timeout': 30,
        'retries': 3,
        'nocheckcertificate': True,
        'fixup': 'never',
        'ffmpeg_location': 'ffmpeg',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        new_filename = None
        try:
            if 'requested_downloads' in info and info['requested_downloads']:
                new_filename = info['requested_downloads'][0].get('filepath')
        except Exception:
            new_filename = None

        if not new_filename:
            new_filename = ydl.prepare_filename(info)
        return new_filename

def download_instagram_video(url):
    """Download the main Instagram video quickly in MP4 when possible.
    Returns the file path.
    """
    downloads_dir = _ensure_download_dir("downloads")
    outtmpl = '%(id)s.%(ext)s'
    if downloads_dir:
        outtmpl = os.path.join(downloads_dir, outtmpl)

    ydl_opts = {
        # Prefer combined MP4 stream to avoid merging
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': outtmpl,
        'socket_timeout': 30,
        'retries': 3,
        'nocheckcertificate': True,
        'fixup': 'never',
        'ffmpeg_location': 'ffmpeg',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        new_filename = None
        try:
            if 'requested_downloads' in info and info['requested_downloads']:
                new_filename = info['requested_downloads'][0].get('filepath')
        except Exception:
            new_filename = None

        if not new_filename:
            new_filename = ydl.prepare_filename(info)
        return new_filename