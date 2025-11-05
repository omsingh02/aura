import asyncio
from shazamio import Shazam

async def recognize_song(audio_file_path):
    try:
        shazam = Shazam()
        result = await shazam.recognize(audio_file_path)
        
        if result and 'track' in result:
            track = result['track']
            return {
                'title': track.get('title', 'Unknown'),
                'artist': track.get('subtitle', 'Unknown'),
                'shazam_count': track.get('shazam_count', 0)
            }
        return None
    except Exception as e:
        print(f'Recognition error: {e}')
        return None
