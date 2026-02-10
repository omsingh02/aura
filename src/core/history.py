import json
import asyncio
from datetime import datetime
from collections import deque
from typing import Optional, Dict, Any, List
from ..config import HISTORY_LIMIT, CACHE_DIR
from ..utils.executor import executor_manager


class SongHistory:
    
    def __init__(self, limit: int = HISTORY_LIMIT):
        self.songs: deque = deque(maxlen=limit)
        self.songs_by_id: Dict[int, Dict[str, Any]] = {}
        self.songs_by_key: Dict[str, Dict[str, Any]] = {}
        self.current: Optional[str] = None
        self.current_index: int = 0
        self.cache_file = CACHE_DIR / "song_history.json"
        self._cache_dirty = False
        self._cache_task: Optional[asyncio.Task] = None
        self._save_counter = 0
        self._load_cache()
    
    def add(self, song_info: Dict[str, Any]) -> tuple[bool, Optional[int]]:
        song_key = f"{song_info['title']}|{song_info['artist']}"
        
        if song_key in self.songs_by_key:
            existing_song = self.songs_by_key[song_key]
            self.current = song_key
            return False, existing_song.get('id')
        
        if len(self.songs) >= self.songs.maxlen:
            oldest_song = self.songs[0]
            oldest_key = f"{oldest_song.get('title', '')}|{oldest_song.get('artist', '')}"
            oldest_id = oldest_song.get('id')
            if oldest_key in self.songs_by_key:
                del self.songs_by_key[oldest_key]
            if oldest_id in self.songs_by_id:
                del self.songs_by_id[oldest_id]
        
        self.current_index += 1
        song_with_id = {
            **song_info,
            'id': self.current_index,
            'detected_at': datetime.now().isoformat()
        }
        self.songs.append(song_with_id)
        self.songs_by_id[self.current_index] = song_with_id
        self.songs_by_key[song_key] = song_with_id
        self.current = song_key
        
        song_info['id'] = self.current_index
        
        self._cache_dirty = True
        self._save_counter += 1
        if self._save_counter >= 10:
            self._schedule_cache_save()
            self._save_counter = 0
        
        self._log_detection(song_with_id)
        return True, self.current_index
    
    def remove(self, song_id: int) -> bool:
        """Remove a song by its ID."""
        if song_id not in self.songs_by_id:
            return False
            
        song = self.songs_by_id.pop(song_id)
        song_key = f"{song.get('title', '')}|{song.get('artist', '')}"
        
        if song_key in self.songs_by_key:
            del self.songs_by_key[song_key]
            
        # Reconstruct deque without the removed song
        self.songs = deque([s for s in self.songs if s['id'] != song_id], maxlen=self.songs.maxlen)
        
        self._cache_dirty = True
        self.force_save_cache()
        return True
    
    def get_by_id(self, song_id: int) -> Optional[Dict[str, Any]]:
        return self.songs_by_id.get(song_id)
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self.songs)[-limit:] if self.songs else []
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        if not self.songs:
            return None
        
        return {
            'total': len(self.songs),
            'artists': len(set(s['artist'] for s in self.songs)),
            'avg_shazam_count': sum(s['shazam_count'] for s in self.songs) // len(self.songs) if self.songs else 0
        }
    
    def _schedule_cache_save(self):
        if self._cache_task and not self._cache_task.done():
            self._cache_task.cancel()
        
        self._cache_task = asyncio.create_task(self._async_save_cache())
    
    async def _async_save_cache(self):
        try:
            await asyncio.sleep(0.5)
            
            if self._cache_dirty:
                await executor_manager.run_in_executor(self._save_cache_sync)
                self._cache_dirty = False
                self._save_counter = 0
        except asyncio.CancelledError:
            pass
        except Exception:
            pass  # Silent fail for cache save
    
    def _save_cache_sync(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.songs), f, indent=2)
        except Exception:
            pass  # Silent fail for cache save
    
    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.songs = deque(data, maxlen=HISTORY_LIMIT)
                    
                    self.songs_by_id = {song.get('id'): song for song in self.songs if song.get('id')}
                    self.songs_by_key = {}
                    for song in self.songs:
                        song_key = f"{song.get('title', '')}|{song.get('artist', '')}"
                        if song_key and song_key != '|':
                            self.songs_by_key[song_key] = song
                    
                    if self.songs:
                        self.current_index = max(s.get('id', 0) for s in self.songs)
                        
            except json.JSONDecodeError:
                pass  # Silent fail for corrupted cache
            except Exception:
                pass  # Silent fail for cache load
    
    def force_save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.songs), f, indent=2)
            self._cache_dirty = False
            self._save_counter = 0
        except Exception:
            pass  # Silent fail for cache save
    
    def _log_detection(self, song_info: Dict[str, Any]) -> None:
        """Log detection - currently disabled for performance."""
        pass
    
    async def cleanup(self):
        if self._cache_task and not self._cache_task.done():
            self._cache_task.cancel()
            try:
                await self._cache_task
            except asyncio.CancelledError:
                pass
        
        self.force_save_cache()
