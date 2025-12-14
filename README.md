# Simvox

A simple Discord music bot. Join a voice channel, play YouTube audio
(by URL or search), and manage a basic queue.

This is still an early alpha — expect bugs and missing features.

## Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and available on your `PATH`
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

## Installation

```bash
git clone <this-repo>
cd simvox
pip install -r requirements.txt
```

Then set up your bot token:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your bot token:

```
TOKEN=your-bot-token-here
```

Finally, run the bot:

```bash
python main.py
```

## Commands

| Command | Description |
|---|---|
| `!join` | Join your current voice channel |
| `!leave` | Leave the voice channel |
| `!play <url or search terms>` | Play a YouTube URL, or search and play the first result (e.g. `!play never gonna give you up`). Adds to the queue if something is already playing |
| `!pause` | Pause the current track |
| `!resume` | Resume a paused track |
| `!skip` | Skip the current track and play the next one in the queue |
| `!queue` | Show what's queued up |
| `!shuffle` | Randomly reorder the queue (the currently playing track is unaffected) |
| `!loop` | Toggle looping the currently playing song on or off |
| `!remove <index>` | Remove a specific song from the queue |
| `!clear` | Clear the queue (the currently playing track keeps playing) |
| `!stop` | Stop playback and clear the queue |
| `!volume [0-200]` | Show the current volume, or set it (default 100%) |

The bot also leaves automatically (and clears its queue) if everyone else
leaves its voice channel, or if it gets disconnected unexpectedly.

## Project structure

```text
simvox/
├── main.py            # entry point — loads config, starts the bot
├── .env.example        # copy to .env and add your token
├── requirements.txt
├── cogs/
│   └── music.py        # user-facing commands
├── core/
│   └── player.py        # per-guild playback state and the play loop
└── utils/
    ├── helpers.py        # yt-dlp extraction
    └── queue.py          # per-guild track queue
```

## Version

v0.1.0-alpha.12