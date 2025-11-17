import asyncio
import speech_recognition as sr
from ..utils.executor import executor_manager

class SpeechTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    async def transcribe_audio(self, audio):
        try:
            text = await executor_manager.run_in_executor(
                self.recognizer.recognize_google, audio
            )
            return text
        except:
            return None
