import subprocess
import sys

try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False

from ..utils.logger import log


class FeedbackManager:
    
    @staticmethod
    def show_notification(title: str, message: str, timeout: int = 5):
        if not NOTIFICATION_AVAILABLE:
            return
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Shazam Live - Voice",
                timeout=timeout
            )
        except Exception as e:
            log(f"Warning: Notification error: {e}", "WARNING")
    
    @staticmethod
    def speak_text(text: str):
        try:
            if sys.platform == "win32":
                ps_command = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{text}")'
                subprocess.Popen(["powershell", "-Command", ps_command], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            elif sys.platform == "darwin":
                subprocess.Popen(["say", text],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["espeak", text],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        except Exception as e:
            log(f"Warning: TTS error: {e}", "WARNING")
    
    @staticmethod
    def is_notification_available() -> bool:
        return NOTIFICATION_AVAILABLE
