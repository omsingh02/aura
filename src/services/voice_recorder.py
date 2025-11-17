import asyncio
import speech_recognition as sr
from pathlib import Path
from ..utils.executor import executor_manager

class VoiceRecorder:
    def __init__(self, recording_duration=6):
        self.recording_duration = recording_duration
        self.recognizer = sr.Recognizer()
    
    async def record_audio(self, audio_file):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = await executor_manager.run_in_executor(
                    lambda: self.recognizer.listen(source, timeout=self.recording_duration)
                )
                with open(audio_file, 'wb') as f:
                    f.write(audio.get_wav_data())
                return audio
        except:
            return None
