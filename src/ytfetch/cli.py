import argparse
import sys
import yt_dlp # type: ignore
from colorama import Fore, Style # type: ignore

# --- Custom Logger ---
class YTFetchLogger:
    def debug(self, msg):
        message = [
            "Downloading playlist:", "Downloading item", "Resuming",
            "Destination:", "already been downloaded",  "Finished downloading"
        ]
        clean_msg = msg.replace("[download] ", "")

        if any(phrase in msg for phrase in message):
            print(clean_msg)

        if "Merging formats" in msg:
            print(msg.replace("[Merger] ", ""))

    def info(self, msg):
        pass

    def warning(self, msg):
        if "Some web client https formats have been skipped" in msg:
            return
        print(f"{msg}")

    def error(self, msg):
        print(f"{msg}")

class ErrorOnlyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)


# --- Custom Progress Hook ---
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0.0%')
        total = d.get('_total_bytes_str', d.get('_total_bytes_estimate_str', 'N/A'))
        speed = d.get('_speed_str', 'N/A')
        status = f"{percent} of {total} at {speed}"
        print(f"\r{status}", end="")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        print()

# --- Argument Parsing ---
def parse_arguments():
    parser = argparse.ArgumentParser(
        usage = "Usage: ytfetch [OPTIONS] URL... [yt-dlp OPTIONS]",
        description="ytfetch: yt-dlp wrapper with flexible args and custom output.",
        epilog = "type yt-dlp -h for yt-dlp options \n"
        "Avoid mixing up options",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-avcmp3", action="store_true",
                        help="Download video in AVC (h.264) format (mp4) + extract audio")
    parser.add_argument("-q", default="1080",
                        help="Video quality (e.g., 1080, 720). Default is 1080.")
    parser.add_argument("-mp3", action="store_true",
                        help="Extract audio only as MP3")
    parser.add_argument("-audio", action="store_true",
                        help="Extract audio only (bestaudio)")
    parser.add_argument("-fetch", nargs="+",
                        help="Alternate for --playlist-items. Single arg applies globally.\n"
                        "Multiple args must match number of playlist URLs provided.")
    parser.add_argument("-list", nargs="?",const="default",
                        help="List playlist contents. Accepts values for searching across playlist")
    parser.add_argument("-o", metavar=f"PATH/{"%""(template)s"}",
                        help="List playlist contents (flat list with playlist name at top)")

    args, unknown_args = parser.parse_known_args()
    return args, unknown_args

def get_urls_from_args(args_list):
    return [a for a in args_list if a.startswith("http")]

def get_format_selector(args):
    height = args.q
    if not args.q == "1080":
        height = args.q.rstrip("p")

    if args.mp3 or args.audio:
        return "bestaudio"

    if args.avcmp3:
        return f"bestvideo[vcodec^=avc1][height<={height}]+bestaudio/best[height<={height}]"
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

def get_post_processors(args):
    post_processors = []
    if args.mp3:
        post_processors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
    elif args.avcmp3:
        post_processors.append({
            'key': 'FFmpegVideoConvertor',
            'preferredformat': 'mp4',
            'postprocessor_args': [
                '-c:v', 'copy',
                '-c:a', 'libmp3lame',
                '-b:a', '192k'
            ]
        })
    return post_processors

def process_urls(custom_args, raw_ytdlp_args):
    urls = get_urls_from_args(raw_ytdlp_args)
    if not urls and not custom_args.list:
        print("Error: No URLs provided.")
        sys.exit(1)

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'logger': YTFetchLogger(),
        'progress_hooks': [progress_hook],
    }

    if custom_args.o:
        ydl_opts['outtmpl'] = custom_args.o

    if custom_args.avcmp3 and not (custom_args.mp3 or custom_args.audio):
        ydl_opts['merge_output_format'] = 'mp4'

    if not custom_args.list:
        ydl_opts['format'] = get_format_selector(custom_args)
        ydl_opts['postprocessors'] = get_post_processors(custom_args)

    # --- Mode: List ---
    if custom_args.list:
        ydl_opts['extract_flat'] = 'in_playlist'
        ydl_opts['logger'] = ErrorOnlyLogger()

        search_mode = False

        # print(custom_args.list)
        if custom_args.list != 'default':
            list_val = str(custom_args.list)
            search_mode = True
            search_pattern = list_val.lower()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  #type: ignore
            for url in urls:
                try:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' not in info:
                        print(f"Single Video: {info.get('title')}")
                        continue
                    print(f"{Fore.CYAN}>{Style.RESET_ALL} Playlist: {Fore.CYAN}{info.get('title')}{Style.RESET_ALL}")
                    print(f"{" -" * 20}")
                    found_match = False
                    for i, entry in enumerate(info['entries'], start=1): #type: ignore
                        # Try to get the actual playlist_index, fallback to enumeration index
                        idx = entry.get('playlist_index', i)
                        title = entry.get('title', 'Unknown')

                        video = f"{Fore.CYAN}{idx:>4}{Style.RESET_ALL} - {title}"

                        if not search_mode:
                            print(video)
                        else:
                            if search_pattern in title.lower():
                                found_match = True
                                print(video)
                    if not found_match and search_mode:
                        print(f"No match found for {Fore.YELLOW}{search_pattern}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"Error listing {url}: {e}")
        return

    # --- Mode: Download ---
    def run_download(url, playlist_items=None):
        opts = ydl_opts.copy()
        if playlist_items:
            opts['playlist_items'] = playlist_items
        with yt_dlp.YoutubeDL(opts) as ydl:  #type:ignore
            try:
                ydl.download([url])
            except Exception as e:
                # print(f"Download error for {url}: {e}")
                pass

    fetch_ranges = custom_args.fetch
    if fetch_ranges:
        if len(fetch_ranges) == 1:
            for url in urls:
                run_download(url, fetch_ranges[0])
        else:
            if len(fetch_ranges) != len(urls):
                print(f"Error: Provided {len(fetch_ranges)} fetch ranges for {len(urls)} URLs.")
                sys.exit(1)
            for url, rng in zip(urls, fetch_ranges):
                run_download(url, rng)
    else:
        for url in urls:
            run_download(url)

def main():
    try:
        custom_args, ytdlp_args = parse_arguments()
        process_urls(custom_args, ytdlp_args)
    except KeyboardInterrupt:
        print("\n\nProcess aborted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()