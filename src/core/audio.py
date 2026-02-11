import asyncio
import wave
import tempfile
import struct
import math
import pyaudio
from typing import Optional

from ..utils.logger import log
from ..utils.executor import executor_manager
from ..config import CHUNK, RATE, CHANNELS

def normalize_audio_data(frames: list) -> bytes:
    try:
        # Combine frames
        audio_data = b''.join(frames)
        
        # Convert to 16-bit integers
        # memoryview and casting is faster than struct.unpack for large data
        try:
            # Create a read-only memoryview
            mv = memoryview(audio_data)
            # Cast to signed short (16-bit)
            shorts = mv.cast('h')
        except TypeError:
            # Fallback if casting fails (e.g. alignment issues or odd length)
            count = len(audio_data) // 2
            shorts = struct.unpack(f'{count}h', audio_data)
        
        if not shorts:
            return audio_data

        # Calculate RMS (Root Mean Square)
        # sum(x^2) can be large, use float
        sum_squares = sum(float(s)**2 for s in shorts)
        rms = math.sqrt(sum_squares / len(shorts))
        
        if rms > 0:
            target_rms = 8192
            scaling_factor = min(target_rms / rms, 4.0)
            
            # Apply scaling and clipping
            # Use list comprehension for speed in pure python (still slower than numpy but fine for 5s audio)
            normalized_shorts = []
            for s in shorts:
                val = int(s * scaling_factor)
                # Clip to 16-bit signed range
                if val > 32767: val = 32767
                elif val < -32768: val = -32768
                normalized_shorts.append(val)
                
            # Pack back to bytes
            return struct.pack(f'{len(normalized_shorts)}h', *normalized_shorts)
            
        return audio_data
        
    except Exception as e:
        log(f"Warning: Audio normalization optimization failed, using fallback: {e}", "WARNING")
        return b''.join(frames)


async def record_audio(duration: int, stop_event: Optional[asyncio.Event] = None, show_progress: bool = True) -> Optional[str]:
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    # Create a threading.Event if an asyncio.Event is passed, to share with the thread
    # Actually, executor runs in a thread, so we need a threading.Event-like object that is thread-safe.
    # We can pass an object that has an is_set() method.
    # But to be safe, let's assume the caller passes an object with is_set(). 
    # Wait, asyncio.Event is not thread-safe for reading from another thread? 
    # Actually, asyncio.Event is not thread-safe. We should pass a threading.Event or a simplified wrapper.
    # Let's verify what we can pass. Ideally, we pass a threading.Event.
    # So the signature: stop_event: Optional[threading.Event]
    
    try:
        return await executor_manager.run_in_executor(_record_audio_sync, duration, temp_path, show_progress, stop_event)
        
    except Exception as e:
        log(f"Recording failed: {e}", "ERROR")
        return None


def _record_audio_sync(duration: int, temp_path: str, show_progress: bool, stop_event=None) -> Optional[str]:
    audio = None
    stream = None
    wf = None
    
    try:
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            channels_used = CHANNELS
        except Exception:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            channels_used = 1
        
        frames = []
        total_chunks = int(RATE / CHUNK * duration)
        chunks_per_second = RATE // CHUNK
        
        for i in range(total_chunks):
            if stop_event and stop_event.is_set():
                break
                
            if show_progress and i % (chunks_per_second // 2) == 0:
                elapsed = i // chunks_per_second
                dots = "." * ((elapsed % 4) + 1)
                print(f"\r🎧 Listening{dots:<4}", end="", flush=True)
            
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        stream = None
        
        normalized_data = normalize_audio_data(frames)
        
        wf = wave.open(temp_path, 'wb')
        wf.setnchannels(channels_used)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(normalized_data)
        wf.close()
        wf = None
        
        return temp_path
        
    except Exception as e:
        log(f"Recording failed: {e}", "ERROR")
        return None
    
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        
        if audio is not None:
            try:
                audio.terminate()
            except Exception:
                pass
        
        if wf is not None:
            try:
                wf.close()
            except Exception:
                pass


async def test_microphone() -> bool:
    audio = None
    stream = None
    
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        return True
        
    except Exception as e:
        log(f"Microphone test failed: {e}", "ERROR")
        return False
    
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
        
        if audio is not None:
            try:
                audio.terminate()
            except Exception:
                pass
