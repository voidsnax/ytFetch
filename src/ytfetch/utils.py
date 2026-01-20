import sys
import argparse
import yt_dlp
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
    def _fill_text(self, text, width, indent):
        # Preserve newlines in Description and Epilog
        # splitlines(keepends=True) ensures not losing of double newlines
        return ''.join(indent + line for line in text.splitlines(keepends=True))

    def _split_lines(self, text, width):
        # Preserve newlines in help
        return text.splitlines()


def print_error(msg):
    print(f"{Fore.RED}{msg}")

def parse_passthrough_args(args_list):
    """
    Parses unknown arguments using yt-dlp's internal parser.
    Returns a dictionary containing ONLY the options explicitly passed by the user.
    """
    filtered_args = [a for a in args_list if not a.startswith("http")]
    if not filtered_args:
        return {}

    parser = yt_dlp.options.create_parser() # type: ignore
    try:
        parsed, _ = parser.parse_known_args(filtered_args)
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
