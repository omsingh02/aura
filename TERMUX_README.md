# Aura on Termux (Android)

Run Aura music recognition on your Android device using Termux!

## Quick Start

### 1. Install Termux
Download from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) or GitHub releases.

### 2. Clone Repository
```bash
git clone <your-repo-url>
cd aura
```

### 3. Run Setup
Choose one of the setup methods:

**Option A: Python Setup (Recommended)**
```bash
python termux-setup.py
```

**Option B: Bash Setup**
```bash
chmod +x termux-setup.sh
./termux-setup.sh
```

### 4. Launch
```bash
./termux-run.sh
```

## Features on Termux

✅ **Working:**
- Live music recognition via Shazam
- Song history tracking
- YouTube search and playback (audio)
- Song downloads
- Voice search
- Terminal UI with keyboard navigation

⚠️ **Limitations:**
- Audio playback is audio-only (no video window)
- May need to grant microphone permission
- Requires stable internet connection
- Desktop notifications not available

## Troubleshooting

### PyAudio Installation Fails
The setup script automatically falls back to `termux-api` for audio recording. Make sure you have:
```bash
pkg install termux-api
```

And install the Termux:API app from F-Droid.

### Microphone Permission Denied
Grant microphone permission:
1. Run the app
2. Android will prompt for permission
3. Or manually: Settings → Apps → Termux → Permissions → Microphone

### "Command not found: mpv"
Install media player:
```bash
pkg install mpv
```

### FFmpeg Not Found
```bash
pkg install ffmpeg
```

### Recording Issues
Test your microphone:
```bash
termux-microphone-record -l 3 -f test.m4a
```

If this works, the app should work too.

### Network Errors
- Check your internet connection
- Some APIs may be blocked on certain networks
- Try using mobile data or VPN

## Manual Installation

If the setup scripts don't work, install manually:

```bash
# Update packages
pkg update && pkg upgrade

# Install system dependencies
pkg install python python-pip portaudio ffmpeg mpv yt-dlp termux-api

# Install Python packages
pip install shazamio numpy jiosaavn-python speechrecognition requests aiohttp rich

# Try PyAudio (optional)
pip install pyaudio

# Run
python -m src.main
```

## Audio Backend

The app uses two audio backends:

1. **PyAudio** (preferred): Direct Python audio capture
2. **termux-api** (fallback): Uses `termux-microphone-record`

The setup script automatically detects and configures the best option.

## Controls

- `↑` / `↓` : Navigate history
- `d` : Download current song
- `y` : Open in YouTube/play
- `v` : Voice search
- `q` : Quit

## Performance Tips

1. **Battery**: Music recognition is CPU-intensive. Keep device charged.
2. **Audio Quality**: Use in quiet environment for best results
3. **Network**: Stable WiFi recommended for downloads
4. **Storage**: Ensure enough space in `/Music/Aura/`

## Permissions Required

- **Microphone**: For audio recording
- **Storage**: For saving songs
- **Network**: For API calls

## Uninstall

```bash
# Remove downloaded songs
rm -rf ~/Music/Aura

# Remove cache
rm -rf ~/.cache/aura

# Uninstall packages (optional)
pip uninstall shazamio jiosaavn-python speechrecognition
pkg uninstall mpv yt-dlp ffmpeg
```

## FAQ

**Q: Can I use this on regular Android?**  
A: No, this requires Termux. For regular Android, you'd need a native app.

**Q: Does it work offline?**  
A: No, requires internet for song recognition and downloads.

**Q: Can I play videos?**  
A: Termux can only play audio. Video playback requires a GUI.

**Q: How much data does it use?**  
A: ~500KB per recognition, plus song download size (3-10MB per song).

**Q: Will this drain my battery?**  
A: Yes, continuous listening uses CPU. Use for short sessions.

## Support

For issues specific to Termux, check:
- [Termux Wiki](https://wiki.termux.com/)
- [Termux GitHub Issues](https://github.com/termux/termux-app/issues)

For app issues, check the main README.md

## Credits

- Shazam-Live: Your project
- Termux: [termux.com](https://termux.com/)
- ShazamIO: Python Shazam library
