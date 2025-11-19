import sys
from pathlib import Path
CHUNK = 2048
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 10
HISTORY_LIMIT = 50
AUTO_DOWNLOAD = False
AUTO_PLAY_YOUTUBE = False
HOME_DIR = Path.home()
DOWNLOAD_DIR = HOME_DIR / "Music" / "ShazamLive"
CACHE_DIR = HOME_DIR / ".cache" / "shazam_live"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def validate_config() -> bool:
    errors = []
    
    if not isinstance(RECORD_SECONDS, (int, float)) or RECORD_SECONDS < 1 or RECORD_SECONDS > 60:
        errors.append(f"RECORD_SECONDS must be between 1 and 60 seconds (got: {RECORD_SECONDS})")
    
    if CHANNELS not in [1, 2]:
        errors.append(f"CHANNELS must be 1 (mono) or 2 (stereo) (got: {CHANNELS})")
    
    valid_rates = [8000, 16000, 22050, 44100, 48000]
    if RATE not in valid_rates:
        errors.append(f"RATE should be one of {valid_rates} (got: {RATE})")
    
    if not isinstance(CHUNK, int) or CHUNK < 256 or CHUNK > 8192:
        errors.append(f"CHUNK must be between 256 and 8192 (got: {CHUNK})")
    
    if not isinstance(HISTORY_LIMIT, int) or HISTORY_LIMIT < 1 or HISTORY_LIMIT > 1000:
        errors.append(f"HISTORY_LIMIT must be between 1 and 1000 (got: {HISTORY_LIMIT})")
    
    try:
        test_file = DOWNLOAD_DIR / ".test_write"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        errors.append(f"DOWNLOAD_DIR is not writable: {DOWNLOAD_DIR} ({e})")
    
    try:
        test_file = CACHE_DIR / ".test_write"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        errors.append(f"CACHE_DIR is not writable: {CACHE_DIR} ({e})")
    
    if errors:
        print("❌ Configuration validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return False
    
    return True
_config_valid = validate_config()
if not _config_valid:
    print("⚠️  Warning: Configuration has errors. Application may not work correctly.", file=sys.stderr)

