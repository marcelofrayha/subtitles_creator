import os
import yt_dlp as youtube_dl

def download_youtube_video(url, progress_callback, output_folder):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_callback],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename

if __name__ == "__main__":
    video_url = input("Enter the YouTube video URL: ")
    output_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    output_file = download_youtube_video(video_url, lambda x: None, output_folder)
    print(f"Video downloaded: {output_file}")
