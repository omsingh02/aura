import asyncio
import subprocess
import sys
from typing import Optional, Tuple
from ..utils.logger import log
from ..utils.executor import executor_manager


class MediaPlayer:
    
    async def get_video_info(self, youtube_url: str, content_type: str = 'song') -> Tuple[Optional[str], Optional[str]]:
        try:
            if content_type in ['trailer', 'video']:
                cmd = ["yt-dlp", "--get-title", youtube_url]
            else:
                cmd = ["yt-dlp", "-f", "bestaudio", "--get-title", "--get-url", youtube_url]
            
            result = await executor_manager.run_in_executor(
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if content_type in ['trailer', 'video']:
                    title = lines[0] if lines else None
                    return title, youtube_url
                else:
                    if len(lines) >= 2:
                        title = lines[0]
                        media_url = lines[1]
                        return title, media_url
            
            return None, None
        except Exception as e:
            log(f"[!] Error getting video info: {e}", "ERROR")
            return None, None
    
    async def play_media(self, media_url: str, title: str, content_type: str = 'song') -> bool:
        try:
            if sys.platform == "win32":
                try:
                    mpv_args = ["mpv"]
                    
                    if content_type in ['trailer', 'video']:
                        mpv_args.extend([
                            "--cache=yes",
                            "--ytdl-format=best",
                            media_url
                        ])
                    else:
                        mpv_args.extend([
                            "--geometry=300x200",
                            media_url
                        ])
                    
                    log(f"> Playing: {title}", "INFO")
                    subprocess.Popen(mpv_args, 
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    return True
                except FileNotFoundError:
                    log("[!] MPV not found, using default Windows player", "WARNING")
                    import webbrowser
                    webbrowser.open(media_url)
                    return True
            else:
                if content_type in ['trailer', 'video']:
                    mpv_args = [
                        "mpv",
                        "--cache=yes",
                        "--ytdl-format=best",
                        media_url
                    ]
                else:
                    mpv_args = ["mpv", media_url]
                
                log(f"▶️ Playing: {title}", "INFO")
                subprocess.Popen(mpv_args,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                return True
        except Exception as e:
            log(f"[!] Playback error: {e}", "ERROR")
            return False
