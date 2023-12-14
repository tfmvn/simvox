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
- `!play <url>` — play a YouTube URL
- `!stop` — stop playback

## Version

v0.1.0-alpha.1
