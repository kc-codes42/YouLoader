# YouLoader
A simple, clean web-based YouTube downloader that runs locally on your machine using yt-dlp.

## Features

- 🎥 Download YouTube videos in various formats
- 🎵 Extract audio in different qualities
- 📱 Clean, responsive web interface
- 📁 Automatic file organization (audio/video folders)
- 🔄 Built-in yt-dlp updater
- 📊 Real-time download progress
- 🎯 Format filtering (audio/video/best quality)
- 📏 File size information when available

## Quick Start

### Option 1: Automatic Setup
1. Save all files in a folder
2. Run: `python setup.py`
3. Run: `python app.py`
4. Open http://localhost:5000

### Option 2: Manual Setup
1. Install requirements: `pip install flask yt-dlp`
2. Install ffmpeg
3. Run: `python app.py`
4. Open http://localhost:5000

## File Structure
```
youtube-downloader/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── setup.py           # Automatic setup script
└── youtubestuff/      # Downloads (created automatically)
    ├── audio/         # Audio files
    └── video/         # Video files
```

## Usage

1. **Paste URL**: Enter a YouTube video URL
2. **Get Formats**: Click to fetch available download formats
3. **Filter**: Use dropdown to filter by audio/video/best quality
4. **Download**: Click download button next to desired format
5. **Monitor**: Watch real-time progress in the status bar

## Requirements

- Python 3.7+
- Internet connection
- Optional: ffmpeg (for best format support)

## Notes

- All downloads are saved locally in the `youtubestuff` folder
- Audio files go to `youtubestuff/audio`
- Video files go to `youtubestuff/video`
- The app automatically creates these folders on first run
- Use the "Update yt-dlp" button to keep the downloader current

## Troubleshooting

- **"No formats found"**: Check if URL is valid YouTube link
- **Download fails**: Try updating yt-dlp or check internet connection
- **Missing formats**: Install ffmpeg for full format support
- **Port in use**: Change port in app.py if 5000 is occupied

## Creator

Built by kc.codes

---

## Security Note

This application is designed for local use only. Do not deploy it to public servers or the internet.
