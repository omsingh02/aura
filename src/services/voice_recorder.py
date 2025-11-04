import asyncio
from pathlib import Path
from typing import Optional

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from ..utils.logger import log
from ..utils.executor import executor_manager


class VoiceRecorder:
    
    def __init__(self, recording_duration: int = 6):
        self.recording_duration = recording_duration
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    async def record_audio(self, audio_file: Path) -> Optional[sr.AudioData]:
        if not self.recognizer:
            log("❌ Speech recognition not available. Install: pip install speechrecognition pyaudio", "ERROR")
            return None
        
        log("🎤 Listening... Speak now!", "INFO")
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                audio = await executor_manager.run_in_executor(
                    lambda: self.recognizer.listen(
                        source, 
                        timeout=self.recording_duration, 
                        phrase_time_limit=self.recording_duration
                    )
                )
                
                with open(audio_file, "wb") as f:
                    f.write(audio.get_wav_data())
                
                return audio
                
        except sr.WaitTimeoutError:
            log("⏱️ No speech detected within timeout period", "WARNING")
            return None
        except Exception as e:
            log(f"❌ Error recording audio: {e}", "ERROR")
            return None
    
    @staticmethod
    def is_available() -> bool:
        return SPEECH_RECOGNITION_AVAILABLE
