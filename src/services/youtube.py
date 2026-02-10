import json
import re
import webbrowser
import aiohttp
from collections import OrderedDict
from typing import Optional
from ..config import CACHE_DIR
from ..utils.logger import log
from ..utils.retry import async_retry
from ..utils.http_session import session_manager


class YouTubePlayer:
    
    MAX_CACHE_SIZE = 500
    
    def __init__(self):
        self.cache_file = CACHE_DIR / "youtube_cache.json"
        self.cache = self._load_cache()
    
    async def play_song(self, song_title: str, artist: str) -> bool:
        try:
            query = f"{song_title} {artist}"
            cache_key = query.lower()
            
            if cache_key in self.cache:
                video_url = self.cache[cache_key]
                log(f"> Playing from cache", "INFO")
            else:
                log(f"[?] Searching YouTube: {query}", "INFO")
                video_url = await self._search_youtube(query)
                
                if video_url:
                    if len(self.cache) >= self.MAX_CACHE_SIZE:
                        self.cache.pop(next(iter(self.cache)))
                    
                    self.cache[cache_key] = video_url
                    self._save_cache()
                else:
                    log("[!] No YouTube results", "WARNING")
                    return False
            
            log(f"[OK] Opening: {video_url}", "SUCCESS")
            webbrowser.open(video_url)
            return True
            
        except Exception as e:
            log(f"[!] YouTube error: {e}", "ERROR")
            return False
    
    @async_retry(max_attempts=3, base_delay=1.0, exceptions=(aiohttp.ClientError, TimeoutError))
    async def _search_youtube(self, query: str) -> Optional[str]:
        try:
            import urllib.parse
            search_query = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={search_query}"
            
            session = await session_manager.get_session()
            async with session.get(search_url) as response:
                response.raise_for_status()
                html = await response.text()
            
            match = re.search(r'"videoId":"([^"]+)"', html)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/watch?v={video_id}"
            
            return None
        except asyncio.CancelledError:
            raise
        except aiohttp.ClientError as e:
            log(f"[!] YouTube HTTP error: {e}", "ERROR")
            return None
        except Exception as e:
            log(f"[!] YouTube search error: {e}", "ERROR")
            return None
    
    def _load_cache(self) -> dict:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                log(f"Warning: Corrupted YouTube cache file: {e}", "WARNING")
                return {}
            except Exception as e:
                log(f"Warning: Could not load YouTube cache: {e}", "WARNING")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            log(f"Warning: Could not save YouTube cache: {e}", "WARNING")
