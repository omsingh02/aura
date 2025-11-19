import os
import asyncio
from typing import Optional, Dict, Any
from shazamio import Shazam
from ..utils.logger import log
from ..utils.retry import async_retry


@async_retry(max_attempts=3, base_delay=2.0, exceptions=(Exception,))
async def recognize_song(audio_file_path: str) -> Optional[Dict[str, Any]]:
    try:
        shazam = Shazam()
        result = await shazam.recognize(audio_file_path)
        
        if result and 'track' in result:
            track = result['track']
            
            song_info = {
                'title': track.get('title', 'Unknown'),
                'artist': track.get('subtitle', 'Unknown'),
                'shazam_count': track.get('shazam_count', 0),
            }
            
            sections = track.get('sections', [])
            if sections:
                metadata = sections[0].get('metadata', [])
                song_info['album'] = metadata[0].get('text', 'Unknown') if len(metadata) > 0 else 'Unknown'
                song_info['release_date'] = metadata[2].get('text', 'Unknown') if len(metadata) > 2 else 'Unknown'
            else:
                song_info['album'] = 'Unknown'
                song_info['release_date'] = 'Unknown'
            
            song_info['genres'] = track.get('genres', {}).get('primary', 'Unknown') if isinstance(track.get('genres'), dict) else 'Unknown'
            
            return song_info
        
        return None
        
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log(f"Recognition error: {e}", "ERROR")
        return None
    finally:
        task = asyncio.create_task(_cleanup_audio_file(audio_file_path))
        task.add_done_callback(lambda t: _handle_cleanup_exception(t, audio_file_path))


def _handle_cleanup_exception(task: asyncio.Task, file_path: str):
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log(f"Warning: Cleanup failed for {file_path}: {e}", "WARNING")


async def _cleanup_audio_file(audio_file_path: str) -> None:
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            if attempt == 0:
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.5 * (2 ** attempt))
            
            if os.path.exists(audio_file_path):
                os.unlink(audio_file_path)
                return
                
        except asyncio.CancelledError:
            raise
        except PermissionError:
            if attempt < max_attempts - 1:
                continue
            else:
                log(f"Warning: File locked after {max_attempts} attempts: {audio_file_path}", "WARNING")
        except Exception as e:
            log(f"Warning: Could not delete temp file {audio_file_path}: {e}", "WARNING")
            break


async def test_shazam() -> bool:
    try:
        shazam = Shazam()
        return True
    except Exception as e:
        log(f"Shazam test failed: {e}", "ERROR")
        return False
