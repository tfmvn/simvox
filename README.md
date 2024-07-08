# Simvox

A very simple Discord music bot. Join a voice channel and play a YouTube URL.

This is an early alpha — expect bugs and missing features.

## Requirements

- Python 3.10+
- FFmpeg installed and on your PATH
- A Discord bot token

## Installation

1. Clone this repo
2. `pip install -r requirements.txt`
3. Copy `config.py.example` to `config.py` and add your bot token
4. Run `python main.py`

## Commands

- `!join` — join your current voice channel
- `!leave` — leave the voice channel
- `!play <url>` — play a YouTube URL, or add it to the queue if something is already playing
- `!pause` — pause the current track
- `!resume` — resume a paused track
- `!skip` — skip the current track and play the next one in the queue
- `!queue` — show what's queued up
- `!remove <index>` — remove a specific song from the queue
- `!clear` — clear the queue (the currently playing track keeps playing)
- `!stop` — stop playback and clear the queue

## Version

v0.1.0-alpha.4