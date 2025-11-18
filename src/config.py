from pathlib import Path

CHUNK = 2048
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 10
HISTORY_LIMIT = 50
AUTO_DOWNLOAD = False
AUTO_PLAY_YOUTUBE = False

HOME_DIR = Path.home()
DOWNLOAD_DIR = HOME_DIR / 'Music' / 'Aura'
CACHE_DIR = HOME_DIR / '.cache' / 'aura'

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
