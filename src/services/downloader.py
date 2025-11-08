import aiohttp
from pathlib import Path

DOWNLOAD_DIR = Path.home() / 'Music' / 'Aura'
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

class MusicDownloader:
    def __init__(self):
        self.output_dir = DOWNLOAD_DIR
    
    async def download_from_jiosaavn(self, song_title, artist):
        try:
            from jiosaavn import JioSaavn
            saavn = JioSaavn()
            query = f'{song_title} {artist}'
            
            results = await saavn.search_songs(query)
            if not results.get('data'):
                return False
            
            song = results['data'][0]
            media_url = await saavn.get_song_direct_link(song['url'])
            
            if not media_url:
                return False
            
            filename = self._sanitize_filename(f'{song_title} - {artist}.m4a')
            filepath = self.output_dir / filename
            
            # Simple download
            async with aiohttp.ClientSession() as session:
                async with session.get(media_url) as response:
                    with open(filepath, 'wb') as f:
                        f.write(await response.read())
            
            print(f'âœ… Downloaded: {filename}')
            return True
        except Exception as e:
            print(f'Download error: {e}')
            return False
    
    def _sanitize_filename(self, filename):
        for char in '<>:\"/\\|?*':
            filename = filename.replace(char, '_')
        return filename
