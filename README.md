# Aura - Terminal Music Assistant

A serverless, terminal-based Shazam client that lets you identify songs, play them on YouTube, and download them directly from your terminal. Built with Python and Rich for a beautiful TUI experience.

## ✨ Features

- **🎵 Song Identification**: Instantly identify songs playing around you using Shazam's recognition technology.
- **🖥️ Beautiful TUI**: A responsive, retro-styled terminal interface built with `rich`.
- **📥 Music Downloader**: Download identified songs directly from JioSaavn in high quality (`.m4a`).
- **▶️ YouTube Integration**: Seamlessly search and play identified songs on YouTube (via browser).
- **🎤 Voice Search**: Use voice commands to search and play music hands-free.
- **📜 History Tracking**: Keeps a local history of all identified songs.
- **📱 Termux Support**: Fully compatible with Android via Termux (see below).

## 🛠️ Prerequisites

- **Python 3.8+**
- **FFmpeg**: Required for audio processing.
  - *Windows*: `winget install ffmpeg`
  - *Linux*: `sudo apt install ffmpeg`
  - *macOS*: `brew install ffmpeg`
- **MPV**: Recommended for in-terminal media playback.
  - *Windows*: `winget install mpv`
  - *Linux*: `sudo apt install mpv`
  - *macOS*: `brew install mpv`
- **PortAudio**: Required for `pyaudio`.
  - *Linux*: `sudo apt install python3-pyaudio portaudio19-dev`

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/omsingh02/aura.git
    cd aura
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/macOS
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 Usage

Run the application:

```bash
python -m src.main
```

### Keyboard Controls

| Key | Action |
| :--- | :--- |
| `↑` / `↓` | Navigate through song history |
| `d` | **Download** the selected song |
| `y` | **Play** the selected song on YouTube (Browser) |
| `v` | **Voice Search** (speak to search) |
| `?` | Toggle Help menu |
| `q` | Quit application |

## ⚙️ Configuration

You can customize the application behavior in `src/config.py`:

- **RECORD_SECONDS**: Duration of audio sample for recognition (default: 10s).
- **DOWNLOAD_DIR**: Directory for downloaded songs (default: `~/Music/ShazamLive`).
- **CACHE_DIR**: Directory for temporary files.
- **HISTORY_LIMIT**: Maximum number of songs to keep in session history.
- **AUTO_DOWNLOAD**: Automatically download identified songs from JioSaavn (default: `False`).
- **AUTO_PLAY_YOUTUBE**: Automatically play identified songs on YouTube (Browser) (default: `False`).

## 📱 Android (Termux) Support

Aura is designed to run on Android devices using Termux. A dedicated setup script handles environment detection and dependency installation specifically for the Termux environment.

**Quick Setup on Termux:**

```bash
python termux-setup.py
./termux-run.sh
```

*Note: On Termux, the app uses `termux-api` for microphone access instead of `pyaudio` if the latter is unavailable.*

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)
