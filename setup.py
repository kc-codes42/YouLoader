
# setup.py - Alternative setup script for automatic installation
#!/usr/bin/env python3
"""
Setup script for YouTube Downloader
Run this first to set up everything automatically
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required Python packages"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "yt-dlp"])
        print("✓ Python packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python packages: {e}")
        return False
    return True

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    import shutil
    if shutil.which("ffmpeg"):
        print("✓ ffmpeg is available")
        return True
    else:
        print("⚠️  ffmpeg not found")
        print("For full functionality, please install ffmpeg:")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt install ffmpeg (Ubuntu/Debian)")
        return False

def create_directories():
    """Create necessary directories"""
    base_dir = Path.cwd() / "youtubestuff"
    audio_dir = base_dir / "audio"
    video_dir = base_dir / "video"
    
    base_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)
    video_dir.mkdir(exist_ok=True)
    
    print(f"✓ Created directories: {base_dir}")

def main():
    print("🎥 YouTube Downloader Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        print("Setup failed. Please install requirements manually.")
        return
    
    # Check ffmpeg
    check_ffmpeg()
    
    # Create directories
    create_directories()
    
    print("\n✅ Setup complete!")
    print("Run 'python app.py' to start the application")
    print("Then open http://localhost:5000 in your browser")

if __name__ == "__main__":
    main()
