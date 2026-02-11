import subprocess
import shutil
import os
import sys

def main():
    # Clean previous builds
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    print("Building Aura Executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name", "ShazamLive",
        "--clean",
        "--hidden-import", "win32timezone",
        "--hidden-import", "shazamio_core",
        "run.py",
        "--exclude-module", "speech_recognition"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild Complete!")
        exe_path = os.path.abspath(os.path.join("dist", "ShazamLive.exe"))
        print(f"Executable located at: {exe_path}")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
