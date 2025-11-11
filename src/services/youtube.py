import webbrowser
import re
import aiohttp

class YouTubePlayer:
    def __init__(self):
        self.cache = {}
    
    async def play_song(self, song_title, artist):
        try:
            query = f'{song_title} {artist}'.replace(' ', '+')
            search_url = f'https://www.youtube.com/results?search_query={query}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    html = await response.text()
            
            match = re.search(r'\"videoId\":\"([^\"]+)\"', html)
            if match:
                video_id = match.group(1)
                url = f'https://www.youtube.com/watch?v={video_id}'
                webbrowser.open(url)
                print(f'âœ… Opening: {url}')
                return True
            return False
        except Exception as e:
            print(f'YouTube error: {e}')
            return False
