import os
from pathlib import Path
import yt_dlp
import sys
from datetime import datetime

def find_closest_resolution(available_heights, target_height):
    """
    Find the closest available resolution to the target height.
    Prefer the next lowest resolution if available.
    """
    if not available_heights:
        return None
    
    # Sort resolutions
    available_heights = sorted(available_heights)
    
    # Try to find the next lowest resolution
    for height in reversed(available_heights):
        if height <= target_height:
            return height
    
    # If no lower resolution, return the lowest available
    return available_heights[0]

def get_video_info(url, resolution="1080p", is_playlist=False):
    """
    Get video or playlist information without downloading.
    Returns video/playlist information including title, format, and filesize.
    """
    target_height = int(resolution[:-1])
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': is_playlist,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ValueError(f"Could not fetch information for {url}")
            
            if is_playlist:
                playlist_title = info.get('title', 'Unknown Playlist')
                entries = info.get('entries', [])
                if not entries:
                    raise ValueError("No videos found in playlist")
                
                videos_info = []
                total_size = 0
                total_duration = 0
                skipped_videos = []
                
                print("\nAnalyzing playlist videos...")
                for i, entry in enumerate(entries, 1):
                    if entry:
                        video_url = entry.get('url')
                        video_title = entry.get('title', 'Unknown Title')
                        if video_url:
                            try:
                                video_info = get_video_info(video_url, resolution, False)
                                videos_info.append(video_info)
                                total_size += video_info['size']
                                total_duration += video_info['duration']
                                print(f"\rAnalyzed {i}/{len(entries)} videos...", end="")
                            except Exception as e:
                                skipped_videos.append({
                                    'title': video_title,
                                    'url': video_url,
                                    'reason': str(e)
                                })
                                print(f"\nSkipping video '{video_title}': {str(e)}")
                
                print("\nPlaylist analysis completed.")
                
                return {
                    'is_playlist': True,
                    'title': playlist_title,
                    'video_count': len(videos_info),
                    'videos': videos_info,
                    'skipped_videos': skipped_videos,
                    'total_size': total_size,
                    'total_duration': total_duration
                }
            
            else:
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                
                formats = info.get('formats', [])
                if not formats:
                    raise ValueError("No formats available for this video")

                # Get available heights
                available_heights = sorted(set(f.get('height', 0) for f in formats if f.get('height')))
                if not available_heights:
                    raise ValueError("No video formats with height information found")

                # Find the best available resolution
                target_height = find_closest_resolution(available_heights, target_height)
                if target_height is None:
                    raise ValueError("No suitable video formats found")

                # Find best video format with selected height
                best_video_format = None
                for f in formats:
                    height = f.get('height', 0)
                    if height == target_height and f.get('vcodec') != 'none':
                        if (best_video_format is None or 
                            f.get('filesize', 0) > best_video_format.get('filesize', 0)):
                            best_video_format = f

                # Find best audio format
                best_audio_format = None
                for f in formats:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        if (best_audio_format is None or 
                            f.get('filesize', 0) > best_audio_format.get('filesize', 0)):
                            best_audio_format = f

                video_size = best_video_format.get('filesize', 0)
                audio_size = best_audio_format.get('filesize', 0) if best_audio_format else 0
                total_size = video_size + audio_size
                
                return {
                    'is_playlist': False,
                    'title': title,
                    'duration': duration,
                    'size': total_size,
                    'resolution': f"{target_height}p",
                    'available_resolutions': [f"{h}p" for h in available_heights]
                }
                
        except Exception as e:
            raise Exception(f"Failed to get info: {str(e)}")

def download_video(url, output_path, resolution="720p"):
    """
    Download a YouTube video or playlist with optimized settings.
    """
    try:
        is_playlist = 'playlist' in url or '&list=' in url
        info = get_video_info(url, resolution, is_playlist)
        
        if is_playlist:
            print("\nPlaylist Information:")
            print(f"Title: {info['title']}")
            print(f"Available videos: {info['video_count']}")
            print(f"Skipped videos: {len(info['skipped_videos'])}")
            total_duration_min = info['total_duration'] / 60
            total_size_mb = info['total_size'] / (1024 * 1024) if info['total_size'] > 0 else 0
            print(f"Total duration: {total_duration_min:.1f} minutes")
            if total_size_mb > 0:
                print(f"Estimated total size: {total_size_mb:.1f} MB")
            else:
                print("Estimated total size: Unknown")
            
            if info['skipped_videos']:
                print("\nSkipped Videos:")
                for vid in info['skipped_videos']:
                    print(f"- {vid['title']}: {vid['reason']}")
        else:
            duration_min = info['duration'] / 60 if info['duration'] > 0 else 0
            filesize_mb = info['size'] / (1024 * 1024) if info['size'] > 0 else 0
            
            print("\nVideo Information:")
            print(f"Title: {info['title']}")
            print(f"Selected Resolution: {info['resolution']}")
            print(f"Available Resolutions: {', '.join(info['available_resolutions'])}")
            print(f"Duration: {duration_min:.1f} minutes")
            if filesize_mb > 0:
                print(f"Estimated size: {filesize_mb:.1f} MB")
            else:
                print("Estimated size: Unknown")
        
        while True:
            response = input("\nDo you want to continue with the download? (y/n): ").lower()
            if response in ['y', 'n']:
                break
            print("Please enter 'y' for yes or 'n' for no.")
        
        if response == 'n':
            print("Download cancelled by user.")
            return
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        ydl_opts = {
            'outtmpl': str(output_dir / f'%(title)s_{timestamp}.%(ext)s'),
            'format': 'bestvideo[height<=144]+bestaudio/best',  # Adjusted format
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'ignoreerrors': True,
            'playlist_items': None,  # Download all videos
            'verbose': True,  # Enable verbose mode
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
            print(f"\nDownload completed! Files saved in: {output_dir}")
            
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

def show_progress(d):
    """Show download progress."""
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', 0)
        filename = d.get('filename', '').split('/')[-1]
        
        if total > 0:
            percent = (downloaded / total) * 100
            speed_mb = speed / (1024 * 1024) if speed else 0
            print(f"\r[{filename}] Progress: {percent:.1f}% | Speed: {speed_mb:.1f}MB/s", end="")
        else:
            downloaded_mb = downloaded / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed else 0
            print(f"\r[{filename}] Downloaded: {downloaded_mb:.1f}MB | Speed: {speed_mb:.1f}MB/s", end="")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ytd.py <video_or_playlist_url> <output_path> [resolution]")
        print("Example: python ytd.py https://www.youtube.com/watch?v=xxx ~/Downloads 1080p")
        print("Example: python ytd.py https://www.youtube.com/playlist?list=xxx ~/Downloads 720p")
        print("\nCommon resolutions:")
        print("1080p - Full HD")
        print("720p  - HD")
        print("480p  - SD")
        print("360p  - Low")
        print("240p  - Lower")
        print("144p  - Lowest")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "1080p"
    
    try:
        download_video(url, output_path, resolution)
    except Exception as e:
        print(f"Error occurred: {str(e)}")