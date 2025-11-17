import asyncio
import sys
import threading
from rich.live import Live
from .ui.tui import AuraTUI
from .services.manager import ServiceManager
from .utils.async_loops import audio_recognition_loop, command_processor_loop

if sys.platform == 'win32':
    import msvcrt
else:
    import select, tty, termios

async def input_reader(command_queue, loop):
    def blocking_input_loop_windows():
        while True:
            try:
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    if char == b'\\x1b':
                        key = 'q'
                    elif char in [b'\\x00', b'\\xe0']:
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
                        key = char.decode('utf-8').lower()
                    asyncio.run_coroutine_threadsafe(command_queue.put(key), loop)
            except:
                pass
    
    input_thread = threading.Thread(target=blocking_input_loop_windows, daemon=True)
    input_thread.start()
    
    while True:
        await asyncio.sleep(1)

async def main_async():
    services = ServiceManager()
    tui = AuraTUI()
    command_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    
    with Live(tui.render(), refresh_per_second=4, screen=True) as live:
        input_task = asyncio.create_task(input_reader(command_queue, loop))
        recognition_task = asyncio.create_task(audio_recognition_loop(services, tui))
        command_task = asyncio.create_task(
            command_processor_loop(services, command_queue, recognition_task, tui)
        )
        
        # Display update loop
        while not command_task.done():
            if tui.needs_render():
                live.update(tui.render())
                tui.mark_rendered()
            await asyncio.sleep(0.05)
        
        recognition_task.cancel()
        input_task.cancel()

def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main_async())

if __name__ == '__main__':
    main()
