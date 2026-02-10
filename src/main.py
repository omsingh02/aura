import asyncio
import sys
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


class InputHandler:
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.queue = queue
        self.loop = loop
        self.running = True
        self._thread = None
        self._setup()

    def _setup(self):
        if sys.platform != 'win32':
            # Unix: Zero-cost add_reader
            try:
                self.loop.add_reader(sys.stdin, self._unix_input_handler)
            except Exception as e:
                log(f"Warning: Stdout not a TTY, falling back to polling: {e}", "WARNING")
                asyncio.create_task(self._fallback_polling_loop())
        else:
            # Windows: Blocking thread
            import threading
            self._thread = threading.Thread(target=self._windows_input_thread, daemon=True)
            self._thread.start()

    def _unix_input_handler(self):
        try:
            line = sys.stdin.read(1)
            if not line:
                return
            
            key = line.lower()
            if key == '\x1b':
                # Simple escape sequence handling
                pass
            
            asyncio.create_task(self.queue.put(key.strip()))
        except Exception:
            pass

    def _windows_input_thread(self):
        """Blocking input thread for Windows - Zero CPU usage"""
        while self.running:
            try:
                # This blocks until a key is pressed - 0% CPU
                char = msvcrt.getch()
                key = ''
                
                if char == b'\x1b':
                    key = 'q'
                elif char == b'\r':
                    continue
                elif char in [b'\x00', b'\xe0']:
                    # Special keys
                    if msvcrt.kbhit():
                        next_char = msvcrt.getch()
                        if next_char == b'H': key = 'up'
                        elif next_char == b'P': key = 'down'
                else:
                    try:
                        key = char.decode('utf-8').lower()
                    except:
                        pass
                
                if key and self.running:
                    # Thread-safe way to put into asyncio queue
                    self.loop.call_soon_threadsafe(self.queue.put_nowait, key)
                    
            except Exception as e:
                # Don't log here to avoid thread conflicts, just retry
                pass

    async def _fallback_polling_loop(self):
        """For non-TTY Unix environments"""
        import select
        while self.running:
            await asyncio.sleep(0.1)

    def stop(self):
        self.running = False
        if sys.platform != 'win32':
            try:
                self.loop.remove_reader(sys.stdin)
            except:
                pass
        # Windows thread is daemon, will die with process


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
            
            # 20Hz check rate is sufficient for TUI
            await asyncio.sleep(0.05)
            
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
        log("[!] System check failed!", "ERROR")
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
        
        # Input handling (No separate task needed for Unix, Task created inside for Win)
        input_handler = InputHandler(command_queue, loop)
        
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
            input_handler.stop()
            update_task.cancel()
            
            await tui.cancel_all_tasks()
            
            cleanup_tasks = [
                services.cleanup(),
                session_manager.close(),
                asyncio.gather(recognition_task, update_task, return_exceptions=True)
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
        log(f"[!] Fatal error: {e}", "ERROR")


if __name__ == "__main__":
    main()
