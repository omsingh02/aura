import asyncio
import aiohttp
from typing import Optional
from ..utils.logger import log


class HTTPSessionManager:
    _instance: Optional['HTTPSessionManager'] = None
    _session: Optional[aiohttp.ClientSession] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
                force_close=False
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=20
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            log("HTTP session created with connection pooling", "INFO")
        
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            try:
                await asyncio.wait_for(self._session.close(), timeout=0.1)
            except asyncio.TimeoutError:
                log("HTTP session close timeout", "WARNING")
            except Exception as e:
                log(f"HTTP session close error: {e}", "WARNING")
            finally:
                self._session = None
    
    def __del__(self):
        pass
session_manager = HTTPSessionManager()
