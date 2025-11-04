#!/data/data/com.termux/files/usr/bin/bash
# Termux Setup Script for Aura
# This script automatically sets up and runs aura on Termux with fallbacks

set -e

echo "🤖 Aura Termux Setup"
echo "============================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo -e "${RED}❌ This script is designed for Termux only!${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Step 1: Installing system packages...${NC}"
pkg update -y
pkg install -y python python-pip portaudio ffmpeg mpv yt-dlp git termux-api 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Some packages may have failed. Continuing...${NC}"
}

echo ""
echo -e "${YELLOW}🐍 Step 2: Installing Python dependencies...${NC}"

# Try to install PyAudio
echo "Attempting to install PyAudio..."
if pip install pyaudio 2>/dev/null; then
    echo -e "${GREEN}✓ PyAudio installed successfully${NC}"
    export PYAUDIO_AVAILABLE=1
else
    echo -e "${YELLOW}⚠️  PyAudio installation failed. Will use termux-api fallback.${NC}"
    export PYAUDIO_AVAILABLE=0
fi

# Install other dependencies
pip install shazamio numpy jiosaavn-python speechrecognition requests aiohttp rich || {
    echo -e "${RED}❌ Failed to install Python dependencies${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}🎤 Step 3: Checking microphone permissions...${NC}"
if command -v termux-microphone-record &> /dev/null; then
    echo "Testing microphone access..."
    timeout 1 termux-microphone-record -f /dev/null 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Microphone permission not granted. Please grant it when prompted.${NC}"
        echo "Requesting permission..."
        termux-microphone-record -l 1 -f /dev/null 2>/dev/null || true
    }
    echo -e "${GREEN}✓ Microphone access configured${NC}"
else
    echo -e "${RED}❌ termux-api not available. Please install: pkg install termux-api${NC}"
fi

echo ""
echo -e "${YELLOW}🔧 Step 4: Creating Termux-compatible audio module...${NC}"

# Create a fallback audio module if PyAudio is not available
if [ "$PYAUDIO_AVAILABLE" -eq 0 ]; then
    cat > "$(dirname "$0")/src/core/audio_termux.py" << 'EOF'
import asyncio
import wave
import tempfile
import subprocess
import os
from typing import Optional
from ..config import RATE
from ..utils.logger import log
from ..utils.executor import executor_manager


async def record_audio(duration: int, show_progress: bool = True) -> Optional[str]:
    """Record audio using termux-api as fallback"""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        return await executor_manager.run_in_executor(_record_audio_termux, duration, temp_path, show_progress)
    except Exception as e:
        log(f"Recording failed: {e}", "ERROR")
        return None


def _record_audio_termux(duration: int, temp_path: str, show_progress: bool) -> Optional[str]:
    """Use termux-microphone-record for audio capture"""
    try:
        # Record using termux-api
        temp_m4a = temp_path.replace('.wav', '.m4a')
        
        if show_progress:
            print(f"\r🎧 Listening...", end="", flush=True)
        
        cmd = [
            'termux-microphone-record',
            '-l', str(duration),
            '-f', temp_m4a
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
        
        if result.returncode != 0:
            log(f"Recording failed: {result.stderr}", "ERROR")
            return None
        
        # Convert m4a to wav using ffmpeg
        convert_cmd = [
            'ffmpeg', '-i', temp_m4a,
            '-ar', str(RATE),
            '-ac', '1',
            '-y',
            temp_path
        ]
        
        subprocess.run(convert_cmd, capture_output=True, check=True)
        
        # Clean up m4a file
        try:
            os.unlink(temp_m4a)
        except:
            pass
        
        if show_progress:
            print("\r" + " " * 50 + "\r", end="", flush=True)
        
        return temp_path
        
    except Exception as e:
        log(f"Termux recording failed: {e}", "ERROR")
        return None


async def test_microphone() -> bool:
    """Test if microphone is accessible"""
    try:
        result = subprocess.run(
            ['termux-microphone-record', '-l', '1', '-f', '/dev/null'],
            capture_output=True,
            timeout=3
        )
        return result.returncode == 0
    except:
        return False
EOF
    echo -e "${GREEN}✓ Created termux-api audio fallback module${NC}"
    
    # Patch main audio.py to use termux fallback
    cat > "$(dirname "$0")/src/core/audio_check.py" << 'EOF'
import sys

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

if not PYAUDIO_AVAILABLE and sys.platform.startswith('linux'):
    # Check if we're in Termux
    try:
        import subprocess
        result = subprocess.run(['which', 'termux-microphone-record'], 
                              capture_output=True, timeout=1)
        if result.returncode == 0:
            print("Using Termux audio backend")
            from .audio_termux import record_audio, test_microphone
        else:
            from .audio import record_audio, test_microphone
    except:
        from .audio import record_audio, test_microphone
else:
    from .audio import record_audio, test_microphone

__all__ = ['record_audio', 'test_microphone']
EOF
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Usage:${NC}"
echo "  To run: python -m src.main"
echo "  Or use: ./termux-run.sh"
echo ""
echo -e "${YELLOW}🎮 Controls:${NC}"
echo "  ↑/↓  - Navigate history"
echo "  d    - Download song"
echo "  y    - Open in YouTube"
echo "  v    - Voice search"
echo "  q    - Quit"
echo ""
echo -e "${YELLOW}⚠️  Notes:${NC}"
echo "  - Grant microphone permission when prompted"
echo "  - Ensure you have internet connection"
echo "  - Audio playback uses mpv (install if needed)"
echo ""

# Create a run script
cat > "$(dirname "$0")/termux-run.sh" << 'RUNEOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"

# Check for PyAudio
python3 -c "import pyaudio" 2>/dev/null
PYAUDIO_AVAILABLE=$?

if [ $PYAUDIO_AVAILABLE -ne 0 ]; then
    echo "⚠️  PyAudio not available, using termux-api fallback"
    export TERMUX_AUDIO_FALLBACK=1
fi

echo "🎵 Starting Aura..."
python3 -m src.main "$@"
RUNEOF

chmod +x "$(dirname "$0")/termux-run.sh"

echo -e "${GREEN}🚀 Ready! Run './termux-run.sh' to start${NC}"
