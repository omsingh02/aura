import asyncio
import sys
import threading
from .core.audio import record_audio
from .core.recognizer import recognize_song
from .core.history import SongHistory
from .services.downloader import MusicDownloader
from .config import RECORD_SECONDS

if sys.platform == 'win32':
    import msvcrt

command_queue = asyncio.Queue()

def input_reader_windows():
    while True:
        if msvcrt.kbhit():
            char = msvcrt.getch()
            try:
                key = char.decode('utf-8').lower()
                asyncio.run_coroutine_threadsafe(
                    command_queue.put(key),
                    asyncio.get_event_loop()
                )
            except:
                pass

async def main():
    history = SongHistory()
    downloader = MusicDownloader()
    
    if sys.platform == 'win32':
        input_thread = threading.Thread(target=input_reader_windows, daemon=True)
        input_thread.start()
    
    print('Music recognition started. Press d to download last song, q to quit.')
    last_song = None
    
    while True:
        try:
            # Check for commands
            if not command_queue.empty():
                cmd = await command_queue.get()
                if cmd == 'q':
                    break
                elif cmd == 'd' and last_song:
                    await downloader.download_from_jiosaavn(
                        last_song['title'],
                        last_song['artist']
                    )
            
            print('\\nListening...')
            audio_file = record_audio(RECORD_SECONDS)
            
            song = await recognize_song(audio_file)
            if song:
                is_new, song_id = history.add(song)
                if is_new:
                    print(f\"âœ“ #{song_id}: {song['title']} by {song['artist']}\")
                    last_song = song
                    
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    asyncio.run(main())
