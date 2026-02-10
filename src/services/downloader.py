import aiohttp
from pathlib import Path
from typing import Optional
from ..config import DOWNLOAD_DIR
from ..utils.logger import log
from ..utils.retry import async_retry
from ..utils.http_session import session_manager


class MusicDownloader:
    
    def __init__(self, output_dir: Path = DOWNLOAD_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_from_jiosaavn(self, song_title: str, artist: str) -> bool:
        try:
            from jiosaavn import JioSaavn
            
            saavn = JioSaavn()
            query = f"{song_title} {artist}"
            
            log(f"[?] Searching JioSaavn: {query}", "INFO")
            results = await saavn.search_songs(query)
            
            if not results.get('data'):
                log("[!] No results on JioSaavn", "WARNING")
                return False
            
            song = results['data'][0]
            song_url = song.get('url')
            
            media_url = await saavn.get_song_direct_link(song_url)
            
            if not media_url:
                log("[!] Could not get download link", "ERROR")
                return False
            
            filename = self._sanitize_filename(f"{song_title} - {artist}.m4a")
            filepath = self.output_dir / filename
            
            success = await self._download_file(media_url, filepath)
            
            if success:
                log(f"[OK] Downloaded: {filename}", "SUCCESS")
                return True
            return False
            
        except ImportError:
            log("[!] JioSaavn library not installed", "ERROR")
            return False
        except Exception as e:
            log(f"[!] Download error: {e}", "ERROR")
            return False
    
    @async_retry(max_attempts=3, base_delay=2.0, exceptions=(aiohttp.ClientError, IOError))
    async def _download_file(self, url: str, filepath: Path) -> bool:
        try:
            headers = {
                'Referer': 'https://www.jiosaavn.com/',
            }
            
            session = await session_manager.get_session()
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
            
            return True
        except aiohttp.ClientError as e:
            log(f"[!] HTTP error during download: {e}", "ERROR")
            return False
        except IOError as e:
            log(f"[!] File I/O error during download: {e}", "ERROR")
            return False
        except Exception as e:
            log(f"[!] Download failed: {e}", "ERROR")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
