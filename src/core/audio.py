import pyaudio
import wave
import tempfile
import numpy as np
from .config import CHUNK, CHANNELS, RATE

def normalize_audio_data(frames):
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
    except:
        return b''.join(frames)

def record_audio(duration):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    frames = []
    for i in range(int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Normalize audio
    normalized_data = normalize_audio_data(frames)
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    wf = wave.open(temp_file.name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(normalized_data)
    wf.close()
    
    return temp_file.name
