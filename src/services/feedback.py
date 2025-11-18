import subprocess
import sys

class FeedbackManager:
    @staticmethod
    def speak_text(text):
        try:
            if sys.platform == 'win32':
                ps_command = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak(\"{text}\")'
                subprocess.Popen(['powershell', '-Command', ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    @staticmethod
    def show_notification(title, message, timeout=5):
        pass  # Optional plyer integration
