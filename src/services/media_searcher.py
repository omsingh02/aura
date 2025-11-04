import asyncio
import aiohttp
import re
import json
from pathlib import Path
from typing import Optional, Tuple
from threading import Lock
from ..config import CACHE_DIR
from ..utils.logger import log
from ..utils.http_session import session_manager
INVIDIOUS_INSTANCES = [
    "https://invidious.tiekoetter.com",
    "https://youtube.com",
    "https://invidious.slipfox.xyz",
    "https://invidious.nerdvpn.de",
    "https://yt.artemislena.eu",
    "https://inv.nadeko.net",
    "https://vid.puffyan.us",
    "https://inv.riverside.rocks",
    "https://invidious.privacydev.net",
    "https://invidious.protokolla.fi",
    "https://invidious.fdn.fr"
]


class MediaSearcher:
    
    def __init__(self, cache_dir: Path = CACHE_DIR / "voice"):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.server_cache_file = self.cache_dir / "server_cache.json"
        self.server_cache = self._load_server_cache()
        self._prioritized_servers = None
        self._cache_dirty = False
        self._cache_lock = Lock()
    
    def _load_server_cache(self) -> dict:
        try:
            if self.server_cache_file.exists():
                with open(self.server_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            log(f"Warning: Error loading server cache: {e}", "WARNING")
        return {}
    
    def _save_server_cache(self):
        try:
            with open(self.server_cache_file, 'w') as f:
                json.dump(self.server_cache, f, indent=2)
        except Exception as e:
            log(f"Warning: Error saving server cache: {e}", "WARNING")
    
    def _update_server_success(self, server: str, success: bool = True):
        with self._cache_lock:
            if server not in self.server_cache:
                self.server_cache[server] = {"success": 0, "fail": 0, "last_used": None}
            
            if success:
                self.server_cache[server]["success"] += 1
                self.server_cache[server]["last_used"] = "recent"
            else:
                self.server_cache[server]["fail"] += 1
            
            self._cache_dirty = True
            self._save_server_cache()
    
    def _get_prioritized_servers(self) -> list:
        with self._cache_lock:
            if self._prioritized_servers is not None and not self._cache_dirty:
                return self._prioritized_servers.copy()
            
            def server_score(server):
                if server not in self.server_cache:
                    return 0
                stats = self.server_cache[server]
                success = stats.get("success", 0)
                fail = stats.get("fail", 0)
                total = success + fail
                
                if total == 0:
                    return 0
                
                success_rate = success / total
                last_used_bonus = 10 if stats.get("last_used") else 0
                
                return (success_rate * 100) + last_used_bonus
            
            self._prioritized_servers = sorted(INVIDIOUS_INSTANCES, key=server_score, reverse=True)
            self._cache_dirty = False
            return self._prioritized_servers.copy()
    
    @staticmethod
    def detect_content_type(query: str) -> str:
        query_lower = query.lower()
        
        trailer_keywords = ['trailer', 'teaser', 'official trailer', 'movie trailer', 'trailer official']
        video_keywords = ['movie', 'film', 'clip', 'scene', 'video']
        
        if any(keyword in query_lower for keyword in trailer_keywords):
            return 'trailer'
        
        if any(keyword in query_lower for keyword in video_keywords):
            return 'video'
        
        return 'song'
    
    async def search_youtube(self, query: str) -> Tuple[Optional[str], str]:
        content_type = self.detect_content_type(query)
        
        if content_type == 'trailer':
            search_query = f"official {query}".replace(" ", "+")
            log(f"🎬 Searching for trailer: {query}", "INFO")
        elif content_type == 'video':
            search_query = f"{query}".replace(" ", "+")
            log(f"🎥 Searching for video: {query}", "INFO")
        else:
            search_query = f"song audio {query}".replace(" ", "+")
            log(f"🎵 Searching for song: {query}", "INFO")
        
        prioritized_servers = self._get_prioritized_servers()
        
        for instance in prioritized_servers:
            try:
                url = f"{instance}/search?q={search_query}"
                
                session = await session_manager.get_session()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    text = await response.text()
                
                match = re.search(r'watch\?v=(.{11})', text)
                if match:
                    video_id = match.group(1)
                    youtube_url = f"https://youtube.com/watch?v={video_id}"
                    log(f"✅ Found: {youtube_url}", "INFO")
                    
                    self._update_server_success(instance, success=True)
                    return youtube_url, content_type
                else:
                    self._update_server_success(instance, success=False)
                    continue
                    
            except aiohttp.ClientError as e:
                log(f"⚠️ HTTP error on {instance}: {type(e).__name__}", "WARNING")
                self._update_server_success(instance, success=False)
                continue
            except Exception as e:
                log(f"⚠️ Failed on {instance}: {type(e).__name__}", "WARNING")
                self._update_server_success(instance, success=False)
                continue
        
        log("❌ All search servers unavailable", "ERROR")
        return None, content_type
