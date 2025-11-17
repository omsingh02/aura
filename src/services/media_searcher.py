import asyncio
import aiohttp
import re
from ..utils.http_session import session_manager

INVIDIOUS_INSTANCES = [
    'https://invidious.tiekoetter.com',
    'https://youtube.com',
    'https://invidious.slipfox.xyz',
]

class MediaSearcher:
    async def search_youtube(self, query):
        content_type = 'song'
        search_query = f'song audio {query}'.replace(' ', '+')
        
        for instance in INVIDIOUS_INSTANCES:
            try:
                url = f'{instance}/search?q={search_query}'
                session = await session_manager.get_session()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    text = await response.text()
                
                match = re.search(r'watch\\?v=(.{11})', text)
                if match:
                    video_id = match.group(1)
                    return f'https://youtube.com/watch?v={video_id}', content_type
            except:
                continue
        return None, content_type
