# Aura

A music recognition app I built because I kept hearing songs and forgetting to Shazam them. This runs continuously in the background and catches everything.

## What it does

- Listens to audio and identifies songs automatically (using Shazam API)
- Voice search - just press 'v' and say what you're looking for
- Downloads songs from JioSaavn 
- Opens songs directly in YouTube
- Keeps a history of everything it finds
- All in a terminal interface because why not

## Setup

You'll need Python 3.8+. Clone this and install the requirements:

```bash
git clone https://github.com/yourusername/aura.git
cd aura
pip install -r requirements.txt
```

Then just run it:
```bash
python -m src.main
```

## How to use

It starts listening immediately. Songs show up as they're recognized.

**Keys:**
- `↑/↓` - scroll through history
- `d` - download the selected song
- `y` - open in YouTube  
- `v` - voice search (speak after pressing)
- `q` - quit

## Config

Check `src/config.py` if you want to change:
- Recording duration (default 10 seconds)
- Download location (default ~/Music/Aura)
- History size
- Auto-download/auto-play settings

## Structure

```
src/
├── core/          # audio capture, recognition, history
├── services/      # downloaders, youtube, search
├── ui/            # terminal interface
└── utils/         # helpers and async stuff
```

## Issues

**PyAudio can be annoying to install:**

Windows: Grab a wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

Linux: `sudo apt-get install portaudio19-dev python3-pyaudio`

macOS: `brew install portaudio && pip install pyaudio`

## Notes

- Downloads are from JioSaavn, quality is pretty good
- Voice recognition needs a decent mic
- Built this mainly for personal use but feel free to use it
- See TERMUX_README.md if you want to run this on Android

## License

MIT - do whatever you want with it
