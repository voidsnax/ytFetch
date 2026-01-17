import sys
import argparse

def validate_fetch_ranges(fetch_ranges, urls):
    if len(fetch_ranges) != len(urls):
        print(f"Error: Provided {len(fetch_ranges)} fetch ranges for {len(urls)} URLs.")
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

