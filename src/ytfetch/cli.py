import argparse
import sys
import yt_dlp # type: ignore
from colorama import Fore, Style # type: ignore
import subprocess
from .utils import (
    validate_fetch_ranges,
    ErrorOnlyLogger,
    AlignedHelpFormatter,
    print_error,
    parse_passthrough_args
    )

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
        print(f"\n{msg}")


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
        usage = "ytfetch [yt-dlp OPTIONS] URL ... [OPTIONS]",
        description="ytfetch: yt-dlp wrapper with flexible args.",
        epilog = "type ytftech -help for yt-dlp options \n"
        "Doc & issues: https://github.com/voidsnax/ytFetch",
        formatter_class=AlignedHelpFormatter,
        add_help=False,
        allow_abbrev=False
    )
    parser.add_argument('-h',action='help',
                        help='Show this help message and exit')
    parser.add_argument('-help',action="store_const",const="default",
                        help='Show yt-dlp help message')

    parser.add_argument("-avcmp3", action="store_true",
                        help="Download video in AVC (h.264) & audio in mp3 format")
    parser.add_argument("-q", metavar="QUALITY",default="1080",
                        help="Video quality (e.g., 1080, 720). Default is 1080")
    parser.add_argument("-mp3", action="store_true",
                        help="Extract audio only as MP3")
    parser.add_argument("-audio", action="store_true",
                        help="Extract audio only (bestaudio)")
    parser.add_argument("-fetch", metavar="RANGE",nargs="+",
                        help="Alternate for --playlist-items. Single value applies globally\n"
                        "Multiple values must match number of playlist URLs provided")
    parser.add_argument("-list", metavar="NAME",nargs="?",const="default",
                        help="List playlist contents. Accepts values for searching across playlist")

    args, unknown_args = parser.parse_known_args()
    return args, unknown_args

def get_urls_from_args(args_list):
    return [a for a in args_list if a.startswith("http")]

def get_format_selector(args):
    height = args.q.rstrip("p")

    if args.mp3 or args.audio:
        return "bestaudio"

    if args.avcmp3:
        return f"bestvideo[vcodec^=avc1][height<={height}]+bestaudio/best[vcodec^=avc1][height<={height}]"
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"


def process_urls(custom_args, raw_ytdlp_args):
    urls = get_urls_from_args(raw_ytdlp_args)
    if custom_args.help:
        yt_dlp.options.create_parser().print_help() # type: ignore
        sys.exit()
    if custom_args.list and custom_args.list.startswith('http'):
        print_error(f"Provided URL link as argument for -list\nUse -list after URL")
        sys.exit(1)
    if custom_args.fetch and any(item.startswith("http") for item in custom_args.fetch):
        print_error(f"Provided a URL link after -fetch\nUse -fetch after URL")
        sys.exit(1)
    if not urls:
        print_error(f"Error: No URLs provided.")
        sys.exit(1)

    passthrough_opts = parse_passthrough_args(raw_ytdlp_args)

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'logger': YTFetchLogger(),
        'progress_hooks': [progress_hook],
    }

    ydl_opts.update(passthrough_opts)

    # --- Mode: List ---
    if custom_args.list:
        base_cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(playlist_index)s - %(title)s"
        ]

        passthrough_args = [arg for arg in raw_ytdlp_args if arg not in urls]
        base_cmd.extend(passthrough_args)
        command = []

        ydl_opts['extract_flat'] = 'in_playlist'
        ydl_opts['logger'] = ErrorOnlyLogger()

        search_mode = False

        fetch_ranges = custom_args.fetch
        if fetch_ranges:
            if len(fetch_ranges) >1:
                validate_fetch_ranges(fetch_ranges,urls)
                for fetch_range in fetch_ranges:
                    command.append(base_cmd + [ "--playlist-items", fetch_range])
            else:
                command.append(base_cmd + ["--playlist-items", fetch_ranges[0]])
        else:
            command.append(base_cmd)

        # make sure command is a list of list
        if len(command) == 1 and len(urls) > 1:
            command = [cmd.copy() for cmd in [command[0]] * len(urls)]

        # print(command)

        if custom_args.list != 'default':
            search_mode = True
            list_val = custom_args.list
            search_pattern = list_val.lower()
        for url, cmd in zip(urls, command):
            # currently for title fetching this is more reliable
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  #type: ignore
                try:
                    info = ydl.extract_info(url, download=False) # type: ignore
                    if 'entries' not in info:
                        print(f"Single Video: {info.get('title')}")
                    else:
                        title = f"▶ Playlist: {info.get('title')}"
                        print(f"▶ Playlist: {Fore.CYAN}{info.get('title')}{Style.RESET_ALL}")
                        print(f"{"-" * len(title)}")
                except Exception as e:
                    print(f"Error getting {url} title: {e}")
            try:
                cmd.append(url)
                # print(cmd)
                result = subprocess.run(cmd, capture_output=True, text=True)
                found_match = False
                for line in result.stdout.splitlines():
                    idx, title = line.split(" - ", 1)
                    video = f"{Fore.YELLOW}{idx}{Style.RESET_ALL} - {title}"
                    if search_mode:
                        if search_pattern in line.lower():
                            found_match = True
                            print(video)
                    else:
                        print(video)
                if not found_match and search_mode:
                    print(f"No match found for {Fore.YELLOW}{search_pattern}{Style.RESET_ALL}")
            except Exception as e:
                print_error(f"Error listing {url}: {e}")

        # stops further execution
        return

    ydl_opts['format'] = get_format_selector(custom_args)

    if custom_args.mp3:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    if custom_args.avcmp3 and not custom_args.mp3:
        ydl_opts['merge_output_format'] = 'mp4'
        ydl_opts['postprocessor_args'] = {
            'ffmpeg': ['-c:v', 'copy', '-c:a', 'libmp3lame', '-b:a', '192k']
        }

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
            validate_fetch_ranges(fetch_ranges,urls)
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
        print(f"\n\n{Fore.YELLOW}Process aborted by user.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()