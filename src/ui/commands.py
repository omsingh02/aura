import asyncio
from typing import Optional
from ..core.history import SongHistory
from ..services.downloader import MusicDownloader
from ..services.youtube import YouTubePlayer
from ..services.voice import VoiceController
from ..utils.logger import log


def _handle_task_exception(task: asyncio.Task, task_name: str):
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log(f"❌ {task_name} task failed: {e}", "ERROR")


async def _run_voice_command(voice_controller, tui):
    try:
        await voice_controller.process_voice_request()
        tui.set_status("Voice command completed")
    except asyncio.CancelledError:
        raise
    except Exception as e:
        tui.set_status(f"❌ Voice error: {str(e)[:30]}")
        raise


async def process_command(
    command: str,
    history: SongHistory,
    downloader: MusicDownloader,
    player: YouTubePlayer,
    iteration: int,
    tui: 'ShazamTUI',
    voice_controller: Optional[VoiceController] = None
) -> Optional[str]:
    cmd = command.strip().lower()
    
    if not cmd:
        return None
    
    if cmd == 'up':
        tui.scroll_up()
        return None
    elif cmd == 'down':
        tui.scroll_down()
        return None
    
    try:
        if cmd == 'd':
            song = tui.get_selected_song()
            
            if song:
                tui.set_status(f"[DL] Downloading: {song['title'][:30]}...")
                task = asyncio.create_task(downloader.download_from_jiosaavn(song['title'], song['artist']))
                task.add_done_callback(lambda t: _handle_task_exception(t, "Download"))
                tui.add_task(task)
            else:
                tui.set_status("❌ No songs detected yet")
        
        elif cmd == 'y':
            song = tui.get_selected_song()
            
            if song:
                tui.set_status(f"[YT] Playing: {song['title'][:30]}...")
                task = asyncio.create_task(player.play_song(song['title'], song['artist']))
                task.add_done_callback(lambda t: _handle_task_exception(t, "YouTube"))
                tui.add_task(task)
            else:
                tui.set_status("❌ No songs detected yet")
        
        elif cmd == 'v':
            if voice_controller:
                tui.set_status("[MIC] Starting voice recognition...")
                task = asyncio.create_task(_run_voice_command(voice_controller, tui))
                task.add_done_callback(lambda t: _handle_task_exception(t, "Voice"))
                tui.add_task(task)
            else:
                tui.set_status("❌ Voice controller not initialized")
        
        elif cmd == '?':
            tui.toggle_help()
        
        elif cmd == 'q':
            return 'quit'
        
        else:
            log(f"❌ Unknown command: {cmd}. Type '?' for help", "WARNING")
    
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log(f"❌ Command error: {e}", "ERROR")
    
    return None
