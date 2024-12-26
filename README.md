# YouTube Downloader

This repository provides two Python scripts for downloading YouTube videos and playlists with advanced options for resolution and file handling. Both scripts use the `yt_dlp` library to ensure reliable and efficient downloads.

## Features

- Download individual YouTube videos with a specified resolution.
- Download entire YouTube playlists while analyzing available resolutions.
- Automatic selection of optimal video and audio formats.
- Displays video and playlist information, including title, duration, and estimated size.
- Handles skipped videos gracefully in playlists.

---

## Files

1. **`single_video_downloader.py`**
   - Downloads a single video from YouTube.
   - Allows specifying the resolution (`1080p`, `720p`, etc.).
   - Verifies the video details before download.

2. **`playlist_downloader.py`**
   - Downloads all videos in a YouTube playlist.
   - Analyzes each video's resolution and size.
   - Reports skipped videos with reasons for failure.

---

## Requirements

- Python 3.7 or higher
- [`yt_dlp`](https://github.com/yt-dlp/yt-dlp): Install it via pip:
  
  ```bash
  pip install yt-dlp
  ```
### Usage
Single Video Downloader
Run the script with the following syntax:

**python single_video_downloader.py <video_url> <output_directory> [resolution]**
Example:
```sh
python single_video_downloader.py "https://www.youtube.com/watch?v=example" "~/Downloads" 1080p
```
### Playlist Downloader
Run the script with the following syntax:

**python playlist_downloader.py <playlist_url> <output_directory> [resolution]**
Example:

```sh
python playlist_downloader.py "https://www.youtube.com/playlist?list=example" "~/Downloads" 720p
```
