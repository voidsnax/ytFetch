# ytfetch

**ytfetch** simplifies media downloading and playlist management by adding smart Fetching, playlist searching, and streamlined format handling on top of the powerful [yt-dlp](https://github.com/yt-dlp/yt-dlp) engine.

## ✨ Features

* **Smart Fetching:** Apply limits to multiple playlists or map specific ranges in a single download.
* **Search:** Use `-list` to display or search across single or multiple playlists contents.
* **Direct Download:** Single flag to download in legacy `avc/h.264` and `mp3` format and audio only extraction.
* **Video Quality:** Mention preffered video quality directly.
* **Native Compatibility:** Can also pass through any `yt-dlp` flag.
* **Minimal Output logs:** Clean and minimal logs.

## 📋 Requirements

- [Python](https://www.python.org/): 3.8 or higher.
- [FFmpeg](https://ffmpeg.org/) and [FFprobe](https://ffmpeg.org/ffprobe.html): Should available in your system PATH.
Download builds from [here](https://ffmpeg.org/download.html)

    <details>
    <summary>or</summary>

    - On Windows:
        ```bash
        winget install BtbN.FFmpeg.GPL
        ```
        or
        ```bash
        winget install Gyan.FFmpeg
        ```

    - On Termux (android):
        ```bash
        pkg install ffmpeg
        ```

    - On Mac (using Homebrew):
        ```bash
        brew install ffmpeg
        ```

    - On Arch Linux:
        ```bash
        sudo pacman -S ffmpeg
        ```

    - On Ubuntu/Debian:
        ```bash
        sudo apt install ffmpeg
        ```
    </details>
- [Deno](https://deno.com/): Or other JavaScript runtime/engine like [node.js](https://nodejs.org/en) or [bun](https://bun.sh/)

  Check this [guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS) for more info.


## 📦 Installation

### via pip

```bash
pip install ytfetch
```

### via source
```bash
git clone https://github.com/voidsnax/ytFetch.git
cd ytFetch
pip install -e .
```

## 🚀 Usage

### General Syntax and Options

```text
usage: Usage: ytfetch [yt-dlp OPTIONS] URL ... [OPTIONS]

options:
  -h                         Show this help message and exit
  -help                      Show yt-dlp help message
  -avcmp3                    Download video in AVC (h.264) & audio in mp3 format
  -q QUALITY                 Video quality (e.g., 1080, 720). Default is 1080
  -mp3                       Extract audio only as MP3
  -audio                     Extract audio only
  -fetch RANGE [RANGE ...]   Alternate for --playlist-items. Single value applies globally
                             Multiple value must match number of playlist URLs provided
  -list [NAME]               List playlist contents. Accepts values for searching across playlist
```

*Note: Arguments are position-independent except for `-list` and `-fetch` where URLs can't be mentioned after it*.

### Examples

#### Basic Downloading

Download a video at the default quality (1080p)
```bash
ytfetch "VIDEO_URL"
```
Download a video in 720p
```bash
ytfetch "VIDEO_URL" -q 720
```
#### Format Conversion

Download as AVC(H.264) and Mp3 in MP4 Container
```bash
ytfetch "VIDEO_URL" -avcmp3
```
Extract Audio Only in Mp3
```bash
ytfetch "VIDEO_URL" -mp3
```
#### Smart Fetching

Global Limit
```bash
ytfetch "PLAYLIST_URL_1" "PLAYLIST_URL_2" -fetch "1-10"
```
Mapped Ranges
```bash
ytfetch "PLAYLIST_A" "PLAYLIST_B"  -fetch "1-5" "10-15"
```
*Note: The number of fetch arguments must match the number of URLs*

#### Listing and Searching

List a Playlist
```bash
ytfetch "PLAYLIST_URL" -list
```
Search through a playlist
```bash
ytfetch "PLAYLIST_URL" -list "remix"
```
Combined Fetch & Search
```bash
ytfetch "PLAYLIST_URL"  -fetch ":50" -list "search_word"
```

#### Passthrough Options

You can append any standard yt-dlp option to your command. Both long and short flags are supported.

Download via Proxy
```bash
ytfetch --proxy "socks5://127.0.0.1:1080" "VIDEO_URL"
```
Use Cookies
```bash
ytfetch --cookies "cookies.txt" "VIDEO_URL"
```
Limit Speed
```bash
ytfetch -r "500K" "VIDEO_URL"
```

## 🔖 License

MIT License
