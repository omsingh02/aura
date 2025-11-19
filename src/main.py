import asyncio
import sys
import threading
from datetime import datetime
from rich.live import Live

from .core.audio import test_microphone
from .core.recognizer import test_shazam
from .services.manager import ServiceManager
from .ui.tui import ShazamTUI
from .utils.async_loops import audio_recognition_loop, command_processor_loop
from .utils.logger import log
from .utils.http_session import session_manager
from .utils.executor import executor_manager

if sys.platform == 'win32':
    import msvcrt
else:
    import select
    import tty
    import termios


async def input_reader(command_queue: asyncio.Queue, loop) -> None:
    
    def blocking_input_loop_windows():
        import time
        
        while True:
            try:
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    if char == b'\x1b':
                        key = 'q'
                    elif char == b'\r':
                        continue
                    elif char in [b'\x00', b'\xe0']:
                        if msvcrt.kbhit():
                            next_char = msvcrt.getch()
                            if next_char == b'H':
                                key = 'up'
                            elif next_char == b'P':
                                key = 'down'
                            else:
                                continue
                        else:
                            continue
                    else:
                        try:
                            key = char.decode('utf-8').lower()
                        except UnicodeDecodeError:
                            continue
                    
                    asyncio.run_coroutine_threadsafe(command_queue.put(key), loop)
                else:
                    # Ultra-short sleep for instant key detection
                    time.sleep(0.0001)  # 0.1ms = 10000Hz polling
            except KeyboardInterrupt:
                break
            except Exception:
                pass
    
    
    def blocking_input_loop_unix():
        import sys
        
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                try:
                    # Ultra-fast polling for instant key detection
                    if select.select([sys.stdin], [], [], 0.0001)[0]:
                        char = sys.stdin.read(1)
                        
                        if char == '\x1b':
                            if select.select([sys.stdin], [], [], 0.0001)[0]:
                                next_char = sys.stdin.read(1)
                                if next_char == '[':
                                    if select.select([sys.stdin], [], [], 0.0001)[0]:
                                        arrow = sys.stdin.read(1)
                                        if arrow == 'A':
                                            key = 'up'
                                        elif arrow == 'B':
                                            key = 'down'
                                        else:
                                            continue
                                    else:
                                        key = 'q'
                                else:
                                    key = 'q'
                            else:
                                key = 'q'
                        elif char == '\r' or char == '\n':
                            continue
                        else:
                            key = char.lower()
                        
                        asyncio.run_coroutine_threadsafe(command_queue.put(key), loop)
                except KeyboardInterrupt:
                    break
                except Exception:
                    pass
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    blocking_input_loop = blocking_input_loop_windows if sys.platform == 'win32' else blocking_input_loop_unix
    
    input_thread = threading.Thread(target=blocking_input_loop, daemon=True)
    input_thread.start()
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


async def update_display(live: Live, tui: ShazamTUI):
    """Ultra-smooth display update with adaptive rendering"""
    last_render_time = 0
    min_render_interval = 0.033  # 30Hz for smooth motion
    
    while True:
        try:
            import time
            current_time = time.time()
            
            if tui.needs_render():
                # Immediate render for navigation, throttled for other updates
                if tui._force_render:
                    live.update(tui.render())
                    tui.mark_rendered()
                    last_render_time = current_time
                elif (current_time - last_render_time) >= min_render_interval:
                    live.update(tui.render())
                    tui.mark_rendered()
                    last_render_time = current_time
            
            # Ultra-tight loop for instant response
            await asyncio.sleep(0.005)  # 200Hz check rate for silky smooth updates
            
        except asyncio.CancelledError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Display update error: {e}", "WARNING")
            await asyncio.sleep(0.1)


async def main_async() -> None:
    mic_ok, shazam_ok = await asyncio.gather(
        test_microphone(),
        test_shazam()
    )
    
    if not mic_ok or not shazam_ok:
        log("❌ System check failed!", "ERROR")
        return
    
    services = ServiceManager()
    tui = ShazamTUI()
    
    for song in services.history.songs:
        if 'title_display' not in song:
            song['title_display'] = song.get('title', 'Unknown')[:30]
            song['artist_display'] = song.get('artist', 'Unknown')[:25]
            song['genre_display'] = song.get('genres', 'Unknown')[:12]
        if 'time' not in song:
            detected_at = song.get('detected_at', '')
            if detected_at:
                try:
                    dt = datetime.fromisoformat(detected_at)
                    song['time'] = dt.strftime("%H:%M:%S")
                except Exception:
                    song['time'] = '--:--:--'
            else:
                song['time'] = '--:--:--'
        tui.add_song(song, auto_scroll=False)
    
    if tui.songs:
        tui.selected_index = len(tui.songs) - 1
        tui._update_scroll()
    
    command_queue = asyncio.Queue()
    
    loop = asyncio.get_event_loop()
    
    # 30Hz for ultra-smooth navigation (33ms refresh)
    # High enough for smooth motion, low enough to prevent flicker
    with Live(tui.render(), refresh_per_second=30, screen=True) as live:
        tui.live = live
        
        input_task = asyncio.create_task(input_reader(command_queue, loop))
        
        recognition_task = asyncio.create_task(
            audio_recognition_loop(services, tui)
        )
        
        command_task = asyncio.create_task(
            command_processor_loop(services, command_queue, recognition_task, tui)
        )
        
        update_task = asyncio.create_task(update_display(live, tui))
        
        try:
            await command_task
        except KeyboardInterrupt:
            pass
        finally:
            recognition_task.cancel()
            input_task.cancel()
            update_task.cancel()
            
            await tui.cancel_all_tasks()
            
            cleanup_tasks = [
                services.cleanup(),
                session_manager.close(),
                asyncio.gather(recognition_task, input_task, update_task, return_exceptions=True)
            ]
            
            executor_manager.shutdown(wait=False)
            
            try:
                await asyncio.wait_for(asyncio.gather(*cleanup_tasks, return_exceptions=True), timeout=0.3)
            except asyncio.TimeoutError:
                pass


def main() -> None:
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\nExiting...\n")
    except Exception as e:
        log(f"❌ Fatal error: {e}", "ERROR")


if __name__ == "__main__":
    main()
