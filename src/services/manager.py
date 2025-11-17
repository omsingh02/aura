from ..core.history import SongHistory
from .downloader import MusicDownloader
from .youtube import YouTubePlayer

class ServiceManager:
    def __init__(self):
        self.history = SongHistory()
        self.downloader = MusicDownloader()
        self.player = YouTubePlayer()
        self.voice_controller = None
    
    async def cleanup(self):
        await self.history.cleanup()
