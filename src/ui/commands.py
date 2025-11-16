import asyncio

async def process_command(command, history, downloader, player, iteration, tui, voice_controller=None):
    cmd = command.strip().lower()
    
    if cmd == 'up':
        if tui.selected_index > 0:
            tui.selected_index -= 1
            tui._dirty = True
    elif cmd == 'down':
        if tui.selected_index < len(tui.songs) - 1:
            tui.selected_index += 1
            tui._dirty = True
    elif cmd == 'd':
        song = tui.songs[tui.selected_index] if tui.songs else None
        if song:
            tui.set_status(f\"[DL] Downloading: {song['title'][:30]}...\")
            await downloader.download_from_jiosaavn(song['title'], song['artist'])
    elif cmd == 'y':
        song = tui.songs[tui.selected_index] if tui.songs else None
        if song:
            tui.set_status(f\"[YT] Playing: {song['title'][:30]}...\")
            await player.play_song(song['title'], song['artist'])
    elif cmd == 'q':
        return 'quit'
    
    return None
