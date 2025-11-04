import asyncio
from typing import Optional

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from ..utils.logger import log
from ..utils.executor import executor_manager


class SpeechTranscriber:
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    async def transcribe_audio(self, audio: sr.AudioData) -> Optional[str]:
        if not self.recognizer:
            log("❌ Speech recognition not available", "ERROR")
            return None
        
        try:
            log("🔄 Transcribing...", "INFO")
            
            text = await executor_manager.run_in_executor(
                self.recognizer.recognize_google,
                audio
            )
            
            log(f"💬 You said: {text}", "INFO")
            return text
            
        except sr.UnknownValueError:
            log("❌ Could not understand audio", "ERROR")
            return None
        except sr.RequestError as e:
            log(f"❌ Could not request results: {e}", "ERROR")
            return None
        except Exception as e:
            log(f"❌ Transcription error: {e}", "ERROR")
            return None
    
    @staticmethod
    def is_available() -> bool:
        return SPEECH_RECOGNITION_AVAILABLE
