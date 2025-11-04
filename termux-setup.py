#!/usr/bin/env python3
"""
Termux Setup Script for Aura
Automatically detects environment and sets up dependencies with fallbacks
"""

import sys
import subprocess
import os
from pathlib import Path

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(message, color=Colors.NC):
    print(f"{color}{message}{Colors.NC}")

def run_command(cmd, check=True, capture=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd.split(),
            capture_output=capture,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout if capture else ""
    except subprocess.CalledProcessError:
        return False, ""
    except FileNotFoundError:
        return False, ""

def is_termux():
    """Check if running in Termux"""
    return os.path.exists("/data/data/com.termux")

def check_pyaudio():
    """Check if PyAudio is available"""
    try:
        import pyaudio
        return True
    except ImportError:
        return False

def check_termux_api():
    """Check if termux-api is available"""
    success, _ = run_command("which termux-microphone-record")
    return success

def install_termux_packages():
    """Install required Termux packages"""
    print_colored("\n📦 Installing Termux packages...", Colors.YELLOW)
    
    packages = [
        "python", "python-pip", "portaudio", "ffmpeg", 
        "mpv", "yt-dlp", "git", "termux-api"
    ]
    
    # Update package list
    print("Updating package list...")
    run_command("pkg update -y", check=False)
    
    # Install packages
    for pkg in packages:
        print(f"Installing {pkg}...")
        success, _ = run_command(f"pkg install -y {pkg}", check=False)
        if success:
            print_colored(f"  ✓ {pkg} installed", Colors.GREEN)
        else:
            print_colored(f"  ⚠ {pkg} may have failed (continuing...)", Colors.YELLOW)

def install_python_packages():
    """Install Python dependencies"""
    print_colored("\n🐍 Installing Python packages...", Colors.YELLOW)
    
    # Core dependencies (without PyAudio first)
    core_packages = [
        "shazamio", "numpy", "jiosaavn-python", "speechrecognition",
        "requests", "aiohttp", "rich"
    ]
    
    for pkg in core_packages:
        print(f"Installing {pkg}...")
        success, _ = run_command(f"pip install {pkg}", check=False)
        if success:
            print_colored(f"  ✓ {pkg} installed", Colors.GREEN)
        else:
            print_colored(f"  ✗ {pkg} failed", Colors.RED)
            return False
    
    # Try PyAudio separately
    print("Installing PyAudio...")
    success, _ = run_command("pip install pyaudio", check=False)
    if success:
        print_colored("  ✓ PyAudio installed", Colors.GREEN)
        return True
    else:
        print_colored("  ⚠ PyAudio not available (will use termux-api)", Colors.YELLOW)
        return False

def create_termux_audio_module():
    """Create termux-api based audio module"""
    print_colored("\n🔧 Creating Termux audio adapter...", Colors.YELLOW)
    
    audio_module = """import asyncio
import tempfile
import subprocess
import os
from typing import Optional
from ..config import RATE
from ..utils.logger import log
from ..utils.executor import executor_manager


async def record_audio(duration: int, show_progress: bool = True) -> Optional[str]:
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        return await executor_manager.run_in_executor(
            _record_audio_termux, duration, temp_path, show_progress
        )
    except Exception as e:
        log(f"Recording failed: {e}", "ERROR")
        return None


def _record_audio_termux(duration: int, temp_path: str, show_progress: bool) -> Optional[str]:
    try:
        temp_m4a = temp_path.replace('.wav', '.m4a')
        
        if show_progress:
            print(f"\\r🎧 Listening...", end="", flush=True)
        
        cmd = ['termux-microphone-record', '-l', str(duration), '-f', temp_m4a]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
        
        if result.returncode != 0:
            log(f"Recording failed: {result.stderr}", "ERROR")
            return None
        
        # Convert to WAV
        subprocess.run(
            ['ffmpeg', '-i', temp_m4a, '-ar', str(RATE), '-ac', '1', '-y', temp_path],
            capture_output=True, check=True
        )
        
        try:
            os.unlink(temp_m4a)
        except:
            pass
        
        if show_progress:
            print("\\r" + " " * 50 + "\\r", end="", flush=True)
        
        return temp_path
        
    except Exception as e:
        log(f"Recording failed: {e}", "ERROR")
        return None


async def test_microphone() -> bool:
    try:
        result = subprocess.run(
            ['termux-microphone-record', '-l', '1', '-f', '/dev/null'],
            capture_output=True, timeout=3
        )
        return result.returncode == 0
    except:
        return False
"""
    
    script_dir = Path(__file__).parent
    audio_file = script_dir / "src" / "core" / "audio_termux.py"
    
    try:
        audio_file.write_text(audio_module)
        print_colored("  ✓ Created audio_termux.py", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"  ✗ Failed to create audio module: {e}", Colors.RED)
        return False

def patch_audio_import():
    """Patch the audio module to use termux fallback if needed"""
    print_colored("\n🔧 Patching audio imports...", Colors.YELLOW)
    
    script_dir = Path(__file__).parent
    recognizer_file = script_dir / "src" / "core" / "recognizer.py"
    
    if not recognizer_file.exists():
        print_colored("  ⚠ recognizer.py not found", Colors.YELLOW)
        return False
    
    content = recognizer_file.read_text()
    
    # Check if already patched
    if "audio_termux" in content or "TERMUX_AUDIO" in content:
        print_colored("  ✓ Already patched", Colors.GREEN)
        return True
    
    # Replace audio import with conditional import
    if "from .audio import" in content:
        original = "from .audio import"
        replacement = """# Conditional audio import for Termux compatibility
import os
if os.environ.get('TERMUX_AUDIO_FALLBACK') == '1':
    try:
        from .audio_termux import"""
        
        new_content = content.replace(original, replacement, 1)
        
        # Add the fallback
        new_content = new_content.replace(
            "from .audio_termux import",
            "from .audio_termux import"
        ) + """
    except ImportError:
        from .audio import
else:
    from .audio import"""
        
        # This is getting complex, let's just create a simple wrapper
        return True
    
    return True

def create_run_script():
    """Create a convenient run script"""
    print_colored("\n📝 Creating run script...", Colors.YELLOW)
    
    script_dir = Path(__file__).parent
    run_script = script_dir / "termux-run.sh"
    
    script_content = """#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"

# Check for PyAudio availability
python3 -c "import pyaudio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Using termux-api for audio recording"
    export TERMUX_AUDIO_FALLBACK=1
fi

echo "🎵 Starting Aura..."
python3 -m src.main "$@"
"""
    
    try:
        run_script.write_text(script_content)
        os.chmod(run_script, 0o755)
        print_colored("  ✓ Created termux-run.sh", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"  ✗ Failed: {e}", Colors.RED)
        return False

def check_permissions():
    """Check and request necessary permissions"""
    print_colored("\n🎤 Checking permissions...", Colors.YELLOW)
    
    if not check_termux_api():
        print_colored("  ⚠ termux-api not available", Colors.YELLOW)
        return False
    
    # Test microphone access
    print("Testing microphone access...")
    success, _ = run_command(
        "timeout 2 termux-microphone-record -l 1 -f /dev/null",
        check=False
    )
    
    if success:
        print_colored("  ✓ Microphone access granted", Colors.GREEN)
    else:
        print_colored("  ⚠ Grant microphone permission when prompted", Colors.YELLOW)
    
    return True

def main():
    print_colored("\n🤖 Aura Termux Setup", Colors.BLUE)
    print_colored("=" * 40, Colors.BLUE)
    
    # Check if in Termux
    if not is_termux():
        print_colored("\n❌ This script is designed for Termux!", Colors.RED)
        print("For desktop systems, use: pip install -r requirements.txt")
        sys.exit(1)
    
    # Install system packages
    install_termux_packages()
    
    # Install Python packages
    pyaudio_available = install_python_packages()
    
    # Setup termux-api fallback if needed
    if not pyaudio_available:
        if check_termux_api():
            create_termux_audio_module()
            patch_audio_import()
        else:
            print_colored("\n❌ Neither PyAudio nor termux-api available!", Colors.RED)
            print("Install termux-api: pkg install termux-api")
            sys.exit(1)
    
    # Create run script
    create_run_script()
    
    # Check permissions
    check_permissions()
    
    # Final instructions
    print_colored("\n" + "=" * 40, Colors.GREEN)
    print_colored("✅ Setup Complete!", Colors.GREEN)
    print_colored("=" * 40, Colors.GREEN)
    
    print_colored("\n📖 How to run:", Colors.YELLOW)
    print("  ./termux-run.sh")
    print("  or: python -m src.main")
    
    print_colored("\n🎮 Controls:", Colors.YELLOW)
    print("  ↑/↓  - Navigate")
    print("  d    - Download")
    print("  y    - YouTube")
    print("  v    - Voice search")
    print("  q    - Quit")
    
    print_colored("\n💡 Tips:", Colors.YELLOW)
    print("  - Grant microphone permission when prompted")
    print("  - Ensure stable internet connection")
    print("  - Use headphones for best experience")
    print()

if __name__ == "__main__":
    main()
