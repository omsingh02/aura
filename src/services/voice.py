from .voice_recorder import VoiceRecorder
from .speech_transcriber import SpeechTranscriber
from .media_searcher import MediaSearcher
from .media_player import MediaPlayer
from pathlib import Path
from ..config import CACHE_DIR

class VoiceController:
    def __init__(self):
        self.recorder = VoiceRecorder(recording_duration=6)
        self.transcriber = SpeechTranscriber()
        self.searcher = MediaSearcher()
        self.player = MediaPlayer()
        self.audio_file = CACHE_DIR / 'voice' / 'audio.wav'
        self.audio_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def process_voice_request(self):
        audio = await self.recorder.record_audio(self.audio_file)
        if not audio:
            return False
        
        text = await self.transcriber.transcribe_audio(audio)
        if not text:
            return False
        
        youtube_url, content_type = await self.searcher.search_youtube(text)
        if not youtube_url:
            return False
        
        title, media_url = await self.player.get_video_info(youtube_url, content_type)
        if not media_url:
            return False
        
        return await self.player.play_media(media_url, title, content_type)
