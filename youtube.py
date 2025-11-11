import yt_dlp
import os

def _ensure_download_dir(path: str = "downloads") -> str:
    if not os.path.isdir(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            # Fallback to current directory if cannot create
            return ""
    return path

def search_youtube(query):
    """Search YouTube and return top entries quickly.
    Prefer flat extraction to speed up search.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch3',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'socket_timeout': 15,
        'retries': 3,
        'fixup': 'never',
        'ffmpeg_location': 'ffmpeg',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info.get('entries', [])

def search_top_video_id(query):
    """Return top YouTube video id and title for a text query (fast)."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'socket_timeout': 15,
        'retries': 3,
        'fixup': 'never',
        'ffmpeg_location': 'ffmpeg',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        entries = info.get('entries', [])
        if entries:
            entry = entries[0]
            return entry.get('id'), entry.get('title')
        return None, None

def download_from_youtube(video_id_or_url):
    """Download best audio for a given YouTube video id quickly.
    Prefer AAC/M4A to avoid heavy transcoding; store in downloads/.
    Returns the full file path.
    """
    downloads_dir = _ensure_download_dir("downloads")
    outtmpl = '%(id)s.%(ext)s'
    if downloads_dir:
        outtmpl = os.path.join(downloads_dir, outtmpl)

    ydl_opts = {
        # Prefer AAC/M4A, then fallback to best available
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

    # Accept both raw video id and full URL
    url = video_id_or_url if isinstance(video_id_or_url, str) and video_id_or_url.startswith("http") else f"https://www.youtube.com/watch?v={video_id_or_url}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # Try to get precise downloaded file path
        new_filename = None
        try:
            if 'requested_downloads' in info and info['requested_downloads']:
                new_filename = info['requested_downloads'][0].get('filepath')
        except Exception:
            new_filename = None

        if not new_filename:
            new_filename = ydl.prepare_filename(info)

        return new_filename