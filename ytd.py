import os
from pathlib import Path
import yt_dlp
import sys
from datetime import datetime

def get_video_info(url, resolution="1080p"):
    """
    Get video information without downloading.
    Returns video title, selected format, and filesize.
    """
    target_height = int(resolution[:-1])
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ValueError(f"Could not fetch video information for {url}")
            
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            
            # Get filesize information
            formats = info.get('formats', [])
            if not formats:
                raise ValueError("No formats available for this video")

            # Find best video format with height <= target_height
            best_video_format = None
            for f in formats:
                height = f.get('height', 0)
                if height and height <= target_height and f.get('vcodec') != 'none':
                    if (best_video_format is None or 
                        height > best_video_format.get('height', 0)):
                        best_video_format = f

            # Find best audio format
            best_audio_format = None
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    if (best_audio_format is None or 
                        f.get('filesize', 0) > best_audio_format.get('filesize', 0)):
                        best_audio_format = f

            if not best_video_format:
                available_heights = sorted(set(f.get('height', 0) for f in formats if f.get('height')))
                if available_heights:
                    suggest_height = next((h for h in available_heights if h <= target_height), available_heights[0])
                    raise ValueError(f"No format found for {resolution}. Available resolutions: {available_heights}. Try {suggest_height}p")
                else:
                    raise ValueError(f"No suitable video formats found")

            # Calculate total size
            video_size = best_video_format.get('filesize', 0)
            audio_size = best_audio_format.get('filesize', 0) if best_audio_format else 0
            total_size = video_size + audio_size
            
            actual_height = best_video_format.get('height', 0)
            
            return {
                'title': title,
                'duration': duration,
                'size': total_size,
                'resolution': f"{actual_height}p"
            }
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")

def download_video(url, output_path, resolution="1080p"):
    """
    Download a YouTube video with optimized settings for large files.
    """
    # Get video information first
    try:
        video_info = get_video_info(url, resolution)
        filesize_mb = video_info['size'] / (1024 * 1024) if video_info['size'] > 0 else 0
        duration_min = video_info['duration'] / 60 if video_info['duration'] > 0 else 0
        
        # Show video information and prompt for confirmation
        print("\nVideo Information:")
        print(f"Title: {video_info['title']}")
        print(f"Resolution: {video_info['resolution']}")
        print(f"Duration: {duration_min:.1f} minutes")
        if filesize_mb > 0:
            print(f"Estimated size: {filesize_mb:.1f} MB")
        else:
            print("Estimated size: Unknown")
        
        # Ask for confirmation
        while True:
            response = input("\nDo you want to continue with the download? (y/n): ").lower()
            if response in ['y', 'n']:
                break
            print("Please enter 'y' for yes or 'n' for no.")
        
        if response == 'n':
            print("Download cancelled by user.")
            return
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        ydl_opts = {
            'outtmpl': str(output_dir / f'%(title)s_{timestamp}.%(ext)s'),
            'format': f'bestvideo[height<={resolution[:-1]}]+bestaudio/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            
            # Optimization settings
            'concurrent_fragments': 16,
            'buffersize': 1024 * 1024,
            'http_chunk_size': 10485760,
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,
            'retry_sleep': 5,
            'socket_timeout': 30,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [show_progress],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\nStarting download...")
            ydl.download([url])
            print(f"\nDownload completed! File saved in: {output_dir}")
            
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

def show_progress(d):
    """Show download progress."""
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', 0)
        
        if total > 0:
            percent = (downloaded / total) * 100
            speed_mb = speed / (1024 * 1024) if speed else 0
            print(f"\rProgress: {percent:.1f}% | Speed: {speed_mb:.1f}MB/s", end="")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ytd.py <video_url> <output_path> [resolution]")
        print("Example: python ytd.py https://www.youtube.com/watch?v=xxx ~/Downloads 1080p")
        print("\nAvailable resolutions:")
        print("1080p - Full HD")
        print("720p  - HD")
        print("480p  - SD")
        print("360p  - Low")
        sys.exit(1)
    
    video_url = sys.argv[1]
    output_path = sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "1080p"
    
    try:
        download_video(video_url, output_path, resolution)
    except Exception as e:
        print(f"Error occurred: {str(e)}")