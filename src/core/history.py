import json
from pathlib import Path
from collections import deque

HISTORY_FILE = Path.home() / '.cache' / 'aura' / 'history.json'

class SongHistory:
    def __init__(self, limit=50):
        self.songs = deque(maxlen=limit)
        self.songs_by_key = {}
        self._load_cache()
    
    def add(self, song_info):
        song_key = f\"{song_info['title']}|{song_info['artist']}\"
        
        if song_key in self.songs_by_key:
            return False, None
        
        song_info['id'] = len(self.songs) + 1
        self.songs.append(song_info)
        self.songs_by_key[song_key] = song_info
        self._save_cache()
        return True, song_info['id']
    
    def _load_cache(self):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.songs = deque(data, maxlen=50)
                    for song in self.songs:
                        key = f\"{song.get('title')}|{song.get('artist')}\"
                        self.songs_by_key[key] = song
            except:
                pass
    
    def _save_cache(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(list(self.songs), f, indent=2)
        except:
            pass
