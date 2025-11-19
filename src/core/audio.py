import asyncio
import wave
import tempfile
import numpy as np
import pyaudio
from typing import Optional
from ..config import CHUNK, CHANNELS, RATE
from ..utils.logger import log
from ..utils.executor import executor_manager


def normalize_audio_data(frames: list) -> bytes:
    try:
        frame_arrays = [np.frombuffer(frame, dtype=np.int16) for frame in frames]
        audio_data = np.concatenate(frame_arrays)
        rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
        
        if rms > 0:
            target_rms = 8192
            scaling_factor = min(target_rms / rms, 4.0)
            audio_data = audio_data * scaling_factor
            audio_data = np.clip(audio_data, -32768, 32767)
        
        return audio_data.astype(np.int16).tobytes()
    except Exception as e:
        log(f"Warning: Audio normalization optimization failed, using fallback: {e}", "WARNING")
        return b''.join(frames)


async def record_audio(duration: int, show_progress: bool = True) -> Optional[str]:
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        return await executor_manager.run_in_executor(_record_audio_sync, duration, temp_path, show_progress)
        
    except Exception as e:
        log(f"Recording failed: {e}", "ERROR")
        return None


def _record_audio_sync(duration: int, temp_path: str, show_progress: bool) -> Optional[str]:
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
