import sys
import argparse
from colorama import Fore, init # type: ignore

init(autoreset=True)

def validate_fetch_ranges(fetch_ranges, urls):
    if len(fetch_ranges) != len(urls):
        print_error(f"Error: Provided {len(fetch_ranges)} fetch ranges for {len(urls)} URLs.")
        sys.exit(1)

class ErrorOnlyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)

class AlignedHelpFormatter(argparse.HelpFormatter):
    def __init__(self, *args, **kwargs):
        kwargs['max_help_position'] = 35  # default is 24
        super().__init__(*args, **kwargs)

def print_error(msg):
    print(f"{Fore.RED}{msg}")

def parse_passthrough_args(args_list):
    """
    Parses unknown arguments (e.g., --proxy, --no-playlist, -f)
    into a dictionary compatible with yt-dlp options.
    """
    opts = {}
    i = 0
    while i < len(args_list):
        arg = args_list[i]

        # --- Long flags ---
        if arg.startswith("--"):
            if "=" in arg:  # --key=value
                key, val = arg[2:].split("=", 1)
                opts[key.replace('-', '_')] = val
                i += 1
                continue

            key = arg[2:].replace('-', '_')

            if key.startswith("no_"):  # --no-flag
                opts[key[3:]] = False
                i += 1
                continue

            if i + 1 < len(args_list) and not args_list[i+1].startswith("-"):
                if not args_list[i+1].startswith("http"):  # skip URLs
                    opts[key] = args_list[i+1]
                    i += 2
                    continue

            opts[key] = True
            i += 1
            continue

        # --- Short flags ---
        elif arg.startswith("-") and len(arg) > 1:
            # Handle grouped flags like -abc -> a=True, b=True, c=True
            if len(arg) > 2 and not "=" in arg:
                for ch in arg[1:]:
                    opts[ch] = True
                i += 1
                continue

            # Handle -k=value
            if "=" in arg:
                key, val = arg[1:].split("=", 1)
                opts[key] = val
                i += 1
                continue

            key = arg[1:]

            # Handle -k value
            if i + 1 < len(args_list) and not args_list[i+1].startswith("-"):
                if not args_list[i+1].startswith("http"):
                    opts[key] = args_list[i+1]
                    i += 2
                    continue

            # Otherwise boolean short flag
            opts[key] = True
            i += 1
            continue

        else:
            # Not a flag, skip (likely a URL or positional arg)
            i += 1

    return opts