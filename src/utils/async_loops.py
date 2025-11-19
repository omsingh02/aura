import asyncio
from typing import Optional
from ..config import RECORD_SECONDS, AUTO_DOWNLOAD, AUTO_PLAY_YOUTUBE
from ..core.audio import record_audio
from ..core.recognizer import recognize_song
from ..services.manager import ServiceManager
from ..utils.logger import log


def _handle_background_task(task: asyncio.Task, task_name: str):
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log(f"Background {task_name} failed: {e}", "WARNING")


async def audio_recognition_loop(
    services: ServiceManager,
    tui: 'ShazamTUI'
) -> None:
    iteration = 0
    consecutive_fails = 0
    max_fails = 5
    
    while True:
        try:
            iteration += 1
            
            tui.set_status("Listening...")
            
            audio_file = await record_audio(RECORD_SECONDS, show_progress=False)
            
            if not audio_file:
                consecutive_fails += 1
                if consecutive_fails >= max_fails:
                    tui.set_status(f"❌ Failed {max_fails} times. Check microphone!")
                    break
                await asyncio.sleep(0.5)
                continue
            
            tui.set_status("Processing...")
            
            song_info = await recognize_song(audio_file)
            
            if song_info:
                is_new, song_id = services.history.add(song_info)
                consecutive_fails = 0
                
                if is_new:
                    tui.add_song(song_info)
                    tui.set_status(f"✓ Found: {song_info['title'][:30]}")
                    
                    if AUTO_DOWNLOAD:
                        task = asyncio.create_task(
                            services.downloader.download_from_jiosaavn(
                                song_info['title'], song_info['artist']
                            )
                        )
                        task.add_done_callback(lambda t: _handle_background_task(t, "Auto-download"))
                    
                    if AUTO_PLAY_YOUTUBE:
                        task = asyncio.create_task(
                            services.player.play_song(song_info['title'], song_info['artist'])
                        )
                        task.add_done_callback(lambda t: _handle_background_task(t, "Auto-play"))
            else:
                consecutive_fails += 1
                tui.set_status("No match found")
            
        except asyncio.CancelledError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Recognition error: {e}", "ERROR")
            tui.set_status(f"❌ Recognition error: {str(e)[:50]}")
            await asyncio.sleep(1)


async def command_processor_loop(
    services: ServiceManager,
    command_queue: asyncio.Queue,
    recognition_task: asyncio.Task,
    tui: 'ShazamTUI',
    iteration_counter: int = 0
) -> None:
    from ..ui.commands import process_command
    iteration = iteration_counter
    
    while True:
        try:
            command = await command_queue.get()
            iteration += 1
            
            # Handle navigation commands immediately with no delay
            if command == 'up':
                tui.scroll_up()
                # Process next command immediately if available
                continue
            elif command == 'down':
                tui.scroll_down()
                # Process next command immediately if available
                continue
            
            result = await process_command(
                command,
                services.history,
                services.downloader,
                services.player,
                iteration,
                tui,
                services.voice_controller
            )
            
            if result == 'quit':
                recognition_task.cancel()
                break
                
        except asyncio.CancelledError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Command processing error: {e}", "ERROR")
            tui.set_status(f"❌ Command processing error: {str(e)[:50]}")

