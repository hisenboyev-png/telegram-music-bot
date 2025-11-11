import yt_dlp
import os

# Use realistic headers to improve Instagram reliability
DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0 Safari/537.36'
    ),
    'Referer': 'https://www.instagram.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

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
        'noprogress': True,
        'http_headers': DEFAULT_HEADERS,
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
        'noprogress': True,
        'http_headers': DEFAULT_HEADERS,
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

def get_instagram_caption(url: str) -> str | None:
    """Extract a human-readable title/caption from an Instagram URL without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'socket_timeout': 20,
        'retries': 2,
        'nocheckcertificate': True,
        'http_headers': DEFAULT_HEADERS,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            return info.get('title') or info.get('description') or None
    except Exception:
        return None