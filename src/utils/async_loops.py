import asyncio
from ..core.audio import record_audio
from ..core.recognizer import recognize_song
from ..config import RECORD_SECONDS

async def audio_recognition_loop(services, tui):
    iteration = 0
    consecutive_fails = 0
    
    while True:
        try:
            iteration += 1
            tui.set_status('Listening...')
            
            audio_file = await record_audio(RECORD_SECONDS, show_progress=False)
            if not audio_file:
                consecutive_fails += 1
                if consecutive_fails >= 5:
                    tui.set_status('âŒ Failed 5 times. Check microphone!')
                    break
                await asyncio.sleep(0.5)
                continue
            
            tui.set_status('Processing...')
            song_info = await recognize_song(audio_file)
            
            if song_info:
                is_new, song_id = services.history.add(song_info)
                consecutive_fails = 0
                
                if is_new:
                    tui.add_song(song_info)
                    tui.set_status(f\"âœ“ Found: {song_info['title'][:30]}\")
            else:
                consecutive_fails += 1
                tui.set_status('No match found')
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            tui.set_status(f'âŒ Error: {str(e)[:50]}')
            await asyncio.sleep(1)

async def command_processor_loop(services, command_queue, recognition_task, tui):
    from ..ui.commands import process_command
    iteration = 0
    
    while True:
        try:
            command = await command_queue.get()
            iteration += 1
            
            result = await process_command(
                command, services.history, services.downloader,
                services.player, iteration, tui, services.voice_controller
            )
            
            if result == 'quit':
                recognition_task.cancel()
                break
        except asyncio.CancelledError:
            break
