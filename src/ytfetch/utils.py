import sys
import argparse
import yt_dlp
from colorama import Fore, init # type: ignore

init(autoreset=True)

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

class ErrorOnlyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)

class AlignedHelpFormatter(argparse.HelpFormatter):
    def __init__(self, *args, **kwargs):
        kwargs['max_help_position'] = 35  # default is 24
        super().__init__(*args, **kwargs)
    def _fill_text(self, text, width, indent):
        # Preserve newlines in Description and Epilog
        # splitlines(keepends=True) ensures not losing of double newlines
        return ''.join(indent + line for line in text.splitlines(keepends=True))

    def _split_lines(self, text, width):
        # Preserve newlines in help
        return text.splitlines()

def parse_passthrough_args(args_list):
    """
    Parses unknown arguments using yt-dlp's internal parser.
    Returns a dictionary containing ONLY the options explicitly passed by the user.
    """
    parser = yt_dlp.options.create_parser() # type: ignore
    try:
        parsed, _ = parser.parse_known_args(args_list)
    except Exception as e:
        print(e,end='')
        sys.exit(1)

    opts = vars(parsed) # convert to dict

    # Filter out defaults to return ONLY user-provided args
    # create a baseline parser to see what the defaults are
    base_parser = yt_dlp.options.create_parser() # type: ignore
    base_parsed, _ = base_parser.parse_args([])
    base_opts = vars(base_parsed)

    # Build dictionary of only changed items
    final_opts = {}
    for key, value in opts.items():
        # Only keep the option if the user changed it from the default
        if base_opts[key] != value:
            final_opts[key] = value

    return final_opts

def validate_fetch_ranges(fetch_ranges, urls):
    if len(fetch_ranges) != len(urls):
        print_error(f"Error: Provided {len(fetch_ranges)} fetch ranges for {len(urls)} URLs.")
        sys.exit(1)

def print_error(msg):
    print(f"{Fore.RED}{msg}")