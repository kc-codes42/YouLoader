
"""
YouTube Video Downloader - Local Application
A simple web-based YouTube downloader using yt-dlp
"""

import os
import sys
import json
import subprocess
import shutil
import threading
import time
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_from_directory

app = Flask(__name__)

# Configuration
BASE_DIR = Path.cwd()
DOWNLOAD_DIR = BASE_DIR / "youtubestuff"
AUDIO_DIR = DOWNLOAD_DIR / "audio"
VIDEO_DIR = DOWNLOAD_DIR / "video"

# Global status tracking
download_status = {}

class YouTubeDownloader:
    def __init__(self):
        self.setup_directories()
        self.check_dependencies()
    
    def setup_directories(self):
        """Create necessary directories"""
        DOWNLOAD_DIR.mkdir(exist_ok=True)
        AUDIO_DIR.mkdir(exist_ok=True)
        VIDEO_DIR.mkdir(exist_ok=True)
        print(f"✓ Directories created: {DOWNLOAD_DIR}")
    
    def check_dependencies(self):
        """Check and install required dependencies"""
        print("Checking dependencies...")
        
        # Check yt-dlp
        if not self.command_exists("yt-dlp"):
            print("Installing yt-dlp...")
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
        
        # Check ffmpeg
        if not self.command_exists("ffmpeg"):
            print("⚠️  ffmpeg not found. Some formats may not work properly.")
            print("Please install ffmpeg manually for full functionality.")
        
        print("✓ Dependencies checked")
    
    def command_exists(self, command):
        """Check if a command exists in PATH"""
        return shutil.which(command) is not None
    
    def get_video_info(self, url):
        """Get video information and available formats"""
        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {"error": f"Failed to fetch video info: {result.stderr}"}
            
            video_info = json.loads(result.stdout)
            
            # Extract relevant information
            formats = []
            for fmt in video_info.get("formats", []):
                if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none":
                    # Audio only
                    format_type = "audio"
                elif fmt.get("acodec") == "none" and fmt.get("vcodec") != "none":
                    # Video only
                    format_type = "video"
                elif fmt.get("vcodec") != "none" and fmt.get("acodec") != "none":
                    # Video with audio
                    format_type = "video"
                else:
                    continue
                
                format_info = {
                    "format_id": fmt.get("format_id"),
                    "ext": fmt.get("ext"),
                    "quality": fmt.get("format_note", "Unknown"),
                    "filesize": fmt.get("filesize"),
                    "type": format_type,
                    "resolution": fmt.get("resolution"),
                    "fps": fmt.get("fps"),
                    "abr": fmt.get("abr"),
                    "vbr": fmt.get("vbr")
                }
                
                formats.append(format_info)
            
            return {
                "title": video_info.get("title"),
                "duration": video_info.get("duration"),
                "uploader": video_info.get("uploader"),
                "formats": formats
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Request timed out"}
        except Exception as e:
            return {"error": str(e)}
    
    def download_video(self, url, format_id, download_id, convert_to_mp3=False):
        try:
            download_status[download_id] = {"status": "starting", "progress": 0}
            
            # Determine output directory based on format
            info = self.get_video_info(url)
            if "error" in info:
                download_status[download_id] = {"status": "error", "message": info["error"]}
                return
            
            format_info = next((f for f in info["formats"] if f["format_id"] == format_id), None)
            if not format_info:
                download_status[download_id] = {"status": "error", "message": "Format not found"}
                return
            
            is_audio = format_info["type"] == "audio"
            output_dir = AUDIO_DIR if is_audio else VIDEO_DIR
            
            # --- START OF MODIFICATION ---

            if is_audio and convert_to_mp3:
                # Prepare for MP3 conversion
                filename_template = "%(title)s.%(ext)s"
                output_path = str(output_dir / filename_template)
                cmd = [
                    "yt-dlp",
                    "-f", format_id,
                    "-o", output_path,
                    "--no-playlist",
                    "--extract-audio",      # Extract audio stream
                    "--audio-format", "mp3",# Convert to mp3
                    "--audio-quality", "0",  # Best audio quality
                    url
                ]
                download_status[download_id] = {"status": "converting to MP3", "progress": 0}
            else:
                # Original download command
                filename_template = "%(title)s.%(ext)s"
                output_path = str(output_dir / filename_template)
                cmd = [
                    "yt-dlp",
                    "-f", format_id,
                    "-o", output_path,
                    "--no-playlist",
                    url
                ]
                download_status[download_id] = {"status": "downloading", "progress": 0}
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Monitor progress
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    try:
                        # Extract percentage
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                percent = float(part.replace("%", ""))
                                download_status[download_id]["progress"] = percent
                                break
                    except:
                        pass
            
            process.wait()
            
            if process.returncode == 0:
                download_status[download_id] = {"status": "completed", "progress": 100}
            else:
                download_status[download_id] = {"status": "error", "message": "Download failed"}
                
        except Exception as e:
            download_status[download_id] = {"status": "error", "message": str(e)}
    
    def update_yt_dlp(self):
        """Update yt-dlp to latest version"""
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True)
            return {"success": True, "message": "yt-dlp updated successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

# Initialize downloader
downloader = YouTubeDownloader()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #2c3e50;
            --text-secondary: #6c757d;
            --text-muted: #adb5bd;
            --border-color: #dee2e6;
            --accent-color: #667eea;
            --accent-hover: #5a6fd8;
            --success-color: #27ae60;
            --success-hover: #229954;
            --warning-color: #f39c12;
            --error-color: #e74c3c;
            --info-color: #3498db;
            --shadow: 0 10px 30px rgba(0,0,0,0.1);
            --shadow-hover: 0 15px 40px rgba(0,0,0,0.15);
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-header: linear-gradient(135deg, #ff6b6b, #ee5a52);
        }

        [data-theme="dark"] {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #404040;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-muted: #808080;
            --border-color: #404040;
            --shadow: 0 10px 30px rgba(0,0,0,0.3);
            --shadow-hover: 0 15px 40px rgba(0,0,0,0.4);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--gradient-primary);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-primary);
            transition: all 0.3s ease;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: var(--bg-primary);
            border-radius: 20px;
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .header {
            background: var(--gradient-header);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }

        .theme-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .theme-toggle:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
            min-height: 400px;
        }
        
        .input-section {
            margin-bottom: 30px;
        }
        
        .input-group {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        input[type="url"] {
            flex: 1;
            min-width: 300px;
            padding: 18px 20px;
            border: 2px solid var(--border-color);
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        input[type="url"]:focus {
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            padding: 18px 25px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--accent-color);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .btn-secondary:hover {
            background: var(--border-color);
            transform: translateY(-2px);
        }
        
        .btn-download {
            background: var(--success-color);
            color: white;
            padding: 12px 20px;
            font-size: 14px;
            border-radius: 8px;
        }
        
        .btn-download:hover {
            background: var(--success-hover);
            transform: translateY(-1px);
        }

        .btn-mp3 {
            background: var(--warning-color);
            color: white;
        }

        .btn-mp3:hover {
            background: #e67e22;
        }
        
        .filter-section {
            margin: 25px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .filter-section label {
            font-weight: 600;
            color: var(--text-primary);
        }
        
        select {
            padding: 12px 16px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 16px;
            background: var(--bg-primary);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.3s ease;
        }

        select:focus {
            outline: none;
            border-color: var(--accent-color);
        }
        
        .video-info {
            background: var(--bg-secondary);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            border: 1px solid var(--border-color);
        }
        
        .video-info h3 {
            color: var(--text-primary);
            margin-bottom: 10px;
            font-size: 1.4em;
        }

        .video-info p {
            color: var(--text-secondary);
            font-size: 1.1em;
        }
        
        .formats-grid {
            display: grid;
            gap: 20px;
        }
        
        .format-item {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
            gap: 20px;
        }
        
        .format-item:hover {
            box-shadow: var(--shadow-hover);
            transform: translateY(-3px);
            border-color: var(--accent-color);
        }
        
        .format-info {
            flex: 1;
        }
        
        .format-title {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        
        .format-details {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .format-type {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 12px;
        }
        
        .type-audio {
            background: rgba(39, 174, 96, 0.1);
            color: var(--success-color);
        }
        
        .type-video {
            background: rgba(52, 152, 219, 0.1);
            color: var(--info-color);
        }
        
        .status {
            margin: 25px 0;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-weight: 600;
            font-size: 1.1em;
            border: 1px solid transparent;
        }
        
        .status.info {
            background: rgba(52, 152, 219, 0.1);
            color: var(--info-color);
            border-color: rgba(52, 152, 219, 0.2);
        }
        
        .status.success {
            background: rgba(39, 174, 96, 0.1);
            color: var(--success-color);
            border-color: rgba(39, 174, 96, 0.2);
        }
        
        .status.error {
            background: rgba(231, 76, 60, 0.1);
            color: var(--error-color);
            border-color: rgba(231, 76, 60, 0.2);
        }

        .status.downloading {
            background: rgba(102, 126, 234, 0.1);
            color: var(--accent-color);
            border-color: rgba(102, 126, 234, 0.2);
        }
        
        .progress-container {
            margin-top: 15px;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-color), var(--success-color));
            transition: width 0.3s ease;
            border-radius: 4px;
        }

        .progress-text {
            margin-top: 8px;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .hidden {
            display: none !important;
        }
        
        .loading {
            text-align: center;
            padding: 60px 40px;
        }
        
        .spinner {
            border: 4px solid var(--bg-tertiary);
            border-top: 4px solid var(--accent-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 25px;
        }

        .loading-text {
            color: var(--text-secondary);
            font-size: 1.1em;
            margin-bottom: 20px;
        }

        .loading-dots {
            display: inline-block;
            animation: dots 1.5s infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes dots {
            0%, 20% { content: ""; }
            40% { content: "."; }
            60% { content: ".."; }
            80%, 100% { content: "..."; }
        }

        .footer {
            background: var(--bg-secondary);
            padding: 20px 30px;
            text-align: center;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 14px;
        }

        .creator-tag {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--bg-primary);
            border-radius: 20px;
            border: 1px solid var(--border-color);
            font-weight: 600;
            color: var(--text-primary);
            transition: all 0.3s ease;
        }

        .creator-tag:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .creator-icon {
            font-size: 16px;
        }

        @media (max-width: 768px) {
            .input-group {
                flex-direction: column;
            }
            
            input[type="url"] {
                min-width: auto;
            }

            .format-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }

            .header h1 {
                font-size: 2em;
            }

            .theme-toggle {
                top: 15px;
                right: 15px;
                width: 40px;
                height: 40px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark/light mode">
                🌙
            </button>
            <h1>🎥 YouTube Downloader</h1>
            <p>Download YouTube videos and audio locally</p>
        </div>
        
        <div class="content">
            <div class="input-section">
                <div class="input-group">
                    <input type="url" id="urlInput" placeholder="Paste YouTube URL here..." />
                    <button class="btn-primary" onclick="fetchFormats()">
                        <span>🔍</span>
                        Get Formats
                    </button>
                    <button class="btn-secondary" onclick="updateYtDlp()">
                        <span>🔄</span>
                        Update yt-dlp
                    </button>
                </div>
            </div>
            
            <div id="status" class="status hidden"></div>
            
            <div id="loadingSection" class="loading hidden">
                <div class="spinner"></div>
                <p class="loading-text">Fetching video information<span class="loading-dots"></span></p>
            </div>
            
            <div id="videoSection" class="hidden">
                <div class="video-info">
                    <h3 id="videoTitle"></h3>
                    <p id="videoDetails"></p>
                </div>
                
                <div class="filter-section">
                    <label for="formatFilter">Filter formats:</label>
                    <select id="formatFilter" onchange="filterFormats()">
                        <option value="all">All Formats</option>
                        <option value="audio">Audio Only</option>
                        <option value="video">Video Only</option>
                        <option value="best">Best Quality</option>
                    </select>
                </div>
                
                <div id="formatsContainer" class="formats-grid"></div>
            </div>
        </div>

        <div class="footer">
            <div class="creator-tag">
                <span class="creator-icon">👨‍💻</span>
                Built by kc.codes
            </div>
        </div>
    </div>

    <script>
        let currentVideoData = null;
        let downloadInterval = null;
        let currentTheme = localStorage.getItem('theme') || 'light';
        
        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', function() {
            applyTheme(currentTheme);
        });
        
        function toggleTheme() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', currentTheme);
            applyTheme(currentTheme);
        }
        
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const themeToggle = document.querySelector('.theme-toggle');
            if (themeToggle) {
                themeToggle.innerHTML = theme === 'light' ? '🌙' : '☀️';
                themeToggle.title = theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode';
            }
        }
        
        function showStatus(message, type = 'info', progress = null) {
            const status = document.getElementById('status');
            status.className = `status ${type}`;
            status.classList.remove('hidden');
            
            let statusHTML = `<div>${message}</div>`;
            
            if (progress !== null && type === 'downloading') {
                statusHTML += `
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <div class="progress-text">${Math.round(progress)}% complete</div>
                    </div>
                `;
            }
            
            status.innerHTML = statusHTML;
        }
        
        function hideStatus() {
            document.getElementById('status').classList.add('hidden');
        }
        
        function showLoading() {
            document.getElementById('loadingSection').classList.remove('hidden');
            document.getElementById('videoSection').classList.add('hidden');
            hideStatus();
        }
        
        function hideLoading() {
            document.getElementById('loadingSection').classList.add('hidden');
        }
        
        async function fetchFormats() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) {
                showStatus('Please enter a YouTube URL', 'error');
                return;
            }
            
            showLoading();
            
            try {
                const response = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showStatus(data.error, 'error');
                    hideLoading();
                    return;
                }
                
                currentVideoData = data;
                displayVideoInfo(data);
                hideLoading();
                
            } catch (error) {
                showStatus('Failed to fetch video information', 'error');
                hideLoading();
            }
        }
        
        function displayVideoInfo(data) {
            document.getElementById('videoTitle').textContent = data.title;
            document.getElementById('videoDetails').textContent = 
                `By ${data.uploader} • ${formatDuration(data.duration)}`;
            
            displayFormats(data.formats);
            document.getElementById('videoSection').classList.remove('hidden');
        }
        
        function displayFormats(formats) {
            const container = document.getElementById('formatsContainer');
            container.innerHTML = '';
            
            formats.forEach(format => {
                const formatElement = createFormatElement(format);
                container.appendChild(formatElement);
            });
        }
        
        function createFormatElement(format) {
            const div = document.createElement('div');
            div.className = 'format-item';
            div.setAttribute('data-type', format.type);
            
            const quality = format.resolution || format.quality || 'Unknown';
            const fileSize = format.filesize ? formatFileSize(format.filesize) : 'Unknown size';
            
            let downloadButtons = `
                <button class="btn-download" onclick="downloadFormat('${format.format_id}')">
                    <span>⬇️</span>
                    Download (${format.ext.toUpperCase()})
                </button>
            `;
    
            if (format.type === 'audio') {
                downloadButtons += `
                    <button class="btn-download btn-mp3" onclick="downloadFormat('${format.format_id}', true)">
                        <span>🎵</span>
                        Download as MP3
                    </button>
                `;
            }

            div.innerHTML = `
                <div class="format-info">
                    <div class="format-title">
                        <span class="format-type type-${format.type}">${format.type.toUpperCase()}</span>
                        ${format.ext.toUpperCase()} - ${quality}
                    </div>
                    <div class="format-details">
                        ${fileSize}${format.abr ? ` • ${format.abr}kbps` : ''}${format.fps ? ` • ${format.fps}fps` : ''}
                    </div>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    ${downloadButtons}
                </div>
            `;
            
            return div;
        }
        
        async function downloadFormat(formatId, convertToMp3 = false) {
            const url = document.getElementById('urlInput').value.trim();
            const downloadId = Date.now().toString();
            
            showStatus('Starting download...', 'info');
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        url: url,
                        format_id: formatId,
                        download_id: downloadId,
                        convert_to_mp3: convertToMp3
                    })
                });
                
                if (response.ok) {
                    monitorDownload(downloadId);
                } else {
                    showStatus('Failed to start download', 'error');
                }
                
            } catch (error) {
                showStatus('Download error: ' + error.message, 'error');
            }
        }
        
        function monitorDownload(downloadId) {
            if (downloadInterval) {
                clearInterval(downloadInterval);
            }
            
            downloadInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/status/${downloadId}`);
                    const status = await response.json();
                    
                    if (status.status === 'downloading' || status.status === 'converting to MP3') {
                        const progress = status.progress || 0;
                        showStatus(`Downloading... ${Math.round(progress)}%`, 'downloading', progress);
                    } else if (status.status === 'completed') {
                        showStatus('Download completed successfully! 🎉', 'success');
                        clearInterval(downloadInterval);
                    } else if (status.status === 'error') {
                        showStatus('Download failed: ' + status.message, 'error');
                        clearInterval(downloadInterval);
                    }
                    
                } catch (error) {
                    clearInterval(downloadInterval);
                    showStatus('Download monitoring error', 'error');
                }
            }, 1000);
        }
        
        function filterFormats() {
            const filter = document.getElementById('formatFilter').value;
            const formatItems = document.querySelectorAll('.format-item');
            
            formatItems.forEach(item => {
                const type = item.getAttribute('data-type');
                
                if (filter === 'all') {
                    item.style.display = 'flex';
                } else if (filter === 'best') {
                    // Show only high quality formats
                    const quality = item.textContent.toLowerCase();
                    if (quality.includes('1080p') || quality.includes('720p') || 
                        quality.includes('best') || quality.includes('320') || 
                        quality.includes('256')) {
                        item.style.display = 'flex';
                    } else {
                        item.style.display = 'none';
                    }
                } else if (filter === type) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }
        
        async function updateYtDlp() {
            showStatus('Updating yt-dlp...', 'info');
            
            try {
                const response = await fetch('/api/update', {method: 'POST'});
                const data = await response.json();
                
                if (data.success) {
                    showStatus('yt-dlp updated successfully! ✅', 'success');
                } else {
                    showStatus('Update failed: ' + data.message, 'error');
                }
                
            } catch (error) {
                showStatus('Update error: ' + error.message, 'error');
            }
        }
        
        function formatDuration(seconds) {
            if (!seconds) return 'Unknown duration';
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        
        function formatFileSize(bytes) {
            if (!bytes) return 'Unknown size';
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(1024));
            return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
        }
        
        // Allow Enter key to fetch formats
        document.getElementById('urlInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                fetchFormats();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    info = downloader.get_video_info(url)
    return jsonify(info)

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    format_id = data.get('format_id')
    download_id = data.get('download_id')
    convert_to_mp3 = data.get('convert_to_mp3', False)
    
    if not all([url, format_id, download_id]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Start download in background thread
    thread = threading.Thread(
        target=downloader.download_video,
        args=(url, format_id, download_id, convert_to_mp3)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True})

@app.route('/api/status/<download_id>')
def get_download_status(download_id):
    status = download_status.get(download_id, {"status": "not_found"})
    return jsonify(status)

@app.route('/api/update', methods=['POST'])
def update_yt_dlp():
    result = downloader.update_yt_dlp()
    return jsonify(result)

if __name__ == '__main__':
    print("🎥 YouTube Downloader Starting...")
    print(f"📁 Download directory: {DOWNLOAD_DIR}")
    print("🌐 Open http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop")
    
    app.run(debug=False, host='localhost', port=5000)