from pathlib import Path
from typing import Optional

from .voice_recorder import VoiceRecorder
from .speech_transcriber import SpeechTranscriber
from .media_searcher import MediaSearcher
from .media_player import MediaPlayer
from .feedback import FeedbackManager
from ..config import CACHE_DIR
from ..utils.logger import log
VOICE_CACHE_DIR = CACHE_DIR / "voice"
AUDIO_FILE = VOICE_CACHE_DIR / "audio.wav"
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class VoiceController:
    
    def __init__(self):
        self.recorder = VoiceRecorder(recording_duration=6)
        self.transcriber = SpeechTranscriber()
        self.searcher = MediaSearcher(cache_dir=VOICE_CACHE_DIR)
        self.player = MediaPlayer()
        self.feedback = FeedbackManager()
    
    async def process_voice_request(self) -> bool:
        if not self.recorder.is_available():
            log("❌ Speech recognition not available. Install: pip install speechrecognition pyaudio", "ERROR")
            return False
        self.feedback.show_notification("Shazam Live", "Listening... Speak your song request!")
        audio = await self.recorder.record_audio(AUDIO_FILE)
        if not audio:
            self.feedback.show_notification("Shazam Live", "No speech detected. Please try again.")
            return False
        self.feedback.show_notification("Shazam Live", "Processing your request...")
        text = await self.transcriber.transcribe_audio(audio)
        if not text:
            self.feedback.show_notification("Shazam Live", "Could not understand. Please speak clearly.")
            return False
        self.feedback.speak_text(f"Alright, let me play {text}")
        youtube_url, content_type = await self.searcher.search_youtube(text)
        if not youtube_url:
            self.feedback.show_notification("Shazam Live", "No results found")
            return False
        title, media_url = await self.player.get_video_info(youtube_url, content_type)
        if not media_url:
            self.feedback.show_notification("Shazam Live", "Could not extract media URL")
            return False
        content_icons = {'song': '🎵', 'trailer': '🎬', 'video': '🎥'}
        icon = content_icons.get(content_type, '🎵')
        log(f"{icon} Playing: {title}", "INFO")
        if content_type == 'trailer':
            self.feedback.show_notification("🎬 Playing Trailer", title, timeout=10)
        elif content_type == 'video':
            self.feedback.show_notification("🎥 Playing Video", title, timeout=10)
        else:
            self.feedback.show_notification("🎵 Now Playing", title, timeout=10)
        success = await self.player.play_media(media_url, title, content_type)
        
        return success

