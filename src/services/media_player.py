import asyncio
import subprocess
import sys
from ..utils.executor import executor_manager

class MediaPlayer:
    async def get_video_info(self, youtube_url, content_type='song'):
        try:
            cmd = ['yt-dlp', '-f', 'bestaudio', '--get-title', '--get-url', youtube_url]
            result = await executor_manager.run_in_executor(
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\\n')
                if len(lines) >= 2:
                    return lines[0], lines[1]
            return None, None
        except:
            return None, None
    
    async def play_media(self, media_url, title, content_type='song'):
        try:
            if sys.platform == 'win32':
                import webbrowser
                webbrowser.open(media_url)
            else:
                subprocess.Popen(['mpv', media_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False
