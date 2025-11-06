import asyncio
from .core.audio import record_audio
from .core.recognizer import recognize_song
from .config import RECORD_SECONDS

async def main():
    print('Starting music recognition...')
    
    while True:
        try:
            print('\\nListening...')
            audio_file = record_audio(RECORD_SECONDS)
            
            print('Processing...')
            song = await recognize_song(audio_file)
            
            if song:
                print(f\"âœ“ Found: {song['title']} by {song['artist']}\")
            else:
                print('No match found')
                
        except KeyboardInterrupt:
            print('\\nExiting...')
            break

if __name__ == '__main__':
    asyncio.run(main())
