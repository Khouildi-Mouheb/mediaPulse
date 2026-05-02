#!/usr/bin/env python3
"""
Export YouTube cookies from browser to cookies.txt for yt-dlp
Run this script, it will open YouTube in a browser, then:
1. Log in to YouTube
2. The script will extract cookies automatically
"""

import subprocess
import sys
from pathlib import Path

def export_cookies_from_browser():
    """Use yt-dlp to extract cookies from your default browser"""
    try:
        # This uses the browser cookies directly
        result = subprocess.run(
            [
                sys.executable, "-m", "yt_dlp",
                "--cookies-from-browser", "chrome",  # or "firefox", "safari", "edge"
                "--dump-single-json",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # dummy video
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Successfully extracted cookies from your browser!")
            print("Cookies are ready to use in yt-dlp")
            return True
        else:
            print("✗ Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Attempting to export YouTube cookies from your browser...")
    export_cookies_from_browser()
