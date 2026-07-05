<p align="center">
  <img src="src/assets/icon.png" width="160" alt="Simvox Logo">
</p>

<h1 align="center">Simvox</h1>

<p align="center">
  <strong>🎵 A lightweight, modern, open-source Discord music bot — slash commands, SQLite-powered, built for self-hosting.</strong>
</p>

<p align="center">
  <a href="https://github.com/tfmvn/simvox/releases"><img alt="Version" src="https://img.shields.io/badge/version-1.0.0-E8132A?style=flat-square"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="discord.py" src="https://img.shields.io/badge/discord.py-2.7-5865F2?style=flat-square&logo=discord&logoColor=white">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-E8132A?style=flat-square"></a>
  <a href="https://github.com/tfmvn/simvox/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/tfmvn/simvox?style=flat-square&logo=github&color=E8132A"></a>
  <a href="https://github.com/tfmvn/simvox/network/members"><img alt="Forks" src="https://img.shields.io/github/forks/tfmvn/simvox?style=flat-square&logo=github&color=E8132A"></a>
  <a href="https://github.com/tfmvn/simvox/issues"><img alt="Issues" src="https://img.shields.io/github/issues/tfmvn/simvox?style=flat-square&logo=github"></a>
  <a href="https://github.com/tfmvn/simvox/pulls"><img alt="Pull Requests" src="https://img.shields.io/github/issues-pr/tfmvn/simvox?style=flat-square&logo=github"></a>
  <a href="https://github.com/tfmvn/simvox/releases"><img alt="Release" src="https://img.shields.io/github/release/tfmvn/simvox?style=flat-square&logo=github&color=E8132A"></a>
  <a href="https://github.com/tfmvn/simvox/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/tfmvn/simvox/total?style=flat-square&logo=github&color=E8132A"></a>
  <img alt="Code Style" src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square">
  <img alt="Ruff" src="https://img.shields.io/badge/linter-ruff-265DFF?style=flat-square&logo=python&logoColor=white">
  <img alt="Black" src="https://img.shields.io/badge/formatter-black-000000?style=flat-square">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?style=flat-square">
</p>

<p align="center">
  <a href="#about">About</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-installation">Installation</a> ·
  <a href="#-commands">Commands</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-contributing">Contributing</a> ·
  <a href="#-license">License</a>
</p>

---

## 📑 Table of Contents

- [About](#about)
- [✨ Features](#-features)
- [📸 Screenshots](#-screenshots)
- [📁 Project Structure](#-project-structure)
- [📋 Requirements](#-requirements)
- [🚀 Installation](#-installation)
- [🔐 Environment Variables](#-environment-variables)
- [🏃 Running](#-running)
- [⚙️ Configuration](#️-configuration)
- [💬 Commands](#-commands)
- [🧱 Architecture](#-architecture)
- [📦 Dependencies](#-dependencies)
- [📊 Performance](#-performance)
- [🤝 Contributing](#-contributing)
- [🛠️ Development](#️-development)
- [🗺️ Roadmap](#️-roadmap)
- [❓ FAQ](#-faq)
- [📄 License](#-license)
- [💬 Support](#-support)
- [🙌 Credits](#-credits)

---

## About

**Simvox** is a lightweight, modern, open-source Discord music bot built with [discord.py](https://discordpy.readthedocs.io/). It is fully **slash-command** driven, **asynchronous** from top to bottom, and **SQLite**-powered — meaning no external database, no Redis, and no Docker required to get going.

Simvox was designed with one goal in mind: **a clean, self-hostable music bot you actually understand and control.** Every line of code is readable, every module has a single responsibility, and every feature is one that real Discord servers ask for. There is no telemetry, no premium tier, and no black box.

- 🪶 **Lightweight** — minimal dependencies, single process, one SQLite file.
- 🧩 **Modular architecture** — `cogs/`, `core/`, `db/`, `ui/`, and `utils/` each own a concern.
- ⚡ **Asynchronous** — `asyncio` end-to-end, including non-blocking database access via `aiosqlite`.
- 🎛️ **Slash-command based** — no text prefixes to remember; full discoverability in the Discord client.
- 💾 **SQLite-powered** — queue state, playlists, settings, and stats all persist across restarts.
- 🏠 **Built for self-hosting** — clone, configure, run. That's it.

Simvox is **100% free and open source** under the MIT license. Fork it, host it, extend it, make it yours.

---

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| 🎶 Playback | **Slash Commands** | Full command surface exposed through Discord slash commands. |
| 🎶 Playback | **Queue Management** | Add, remove, move, shuffle, and clear tracks with autocomplete. |
| 🎶 Playback | **Playlists** | Per-user, per-guild playlists persisted in SQLite. |
| 🎶 Playback | **Lyrics** | Real, paginated lyrics for the current or any track. |
| 🎶 Playback | **SponsorBlock** | Automatically skips sponsor segments on YouTube tracks. |
| 🎶 Playback | **Autoplay** | Smart recommendations keep the music going when the queue ends. |
| 🎶 Playback | **Audio Filters** | Bass Boost, Nightcore, Vaporwave, 8D, Karaoke, Treble. |
| 🎶 Playback | **Loop Modes** | Off / Track / Queue, selectable from an interactive view. |
| 🎶 Playback | **Shuffle** | Randomize the queue with one command. |
| 🎶 Playback | **Skip & Vote Skip** | DJ force-skip or democratic vote-skip for everyone. |
| 🎶 Playback | **Seek & Replay** | Jump to a timestamp or restart from the beginning. |
| 🔊 Audio | **Volume** | Adjustable from 0–200, persisted per guild. |
| 🔊 Audio | **Quality Tiers** | Low / Medium / High / Source bitrate selection. |
| ⏱️ Lifecycle | **Idle Disconnect** | Auto-leaves the voice channel after inactivity. |
| ⏱️ Lifecycle | **24/7 Mode** | Stay in voice permanently, ideal for lounge channels. |
| 🛡️ Permissions | **DJ Role** | Restrict playback controls to a designated role. |
| 🛡️ Permissions | **Manage Server Gates** | Settings changes require server admin permission. |
| ⚙️ Config | **Server Settings** | DJ role, SponsorBlock, idle timeout, quality, 24/7 — all in-app. |
| 💾 Persistence | **Queue Persistence** | Survives restarts; restores playback where it left off. |
| 📈 Analytics | **Statistics** | Per-guild listening stats: top tracks, artists, total time. |
| 🔎 Discovery | **Search** | Browse top results without auto-playing. |
| 🔎 Discovery | **Recommendations** | Autoplay uses smart recommendations, not raw title search. |
| 🗄️ Storage | **SQLite Storage** | Single-file database — no external services. |
| 📝 Observability | **Logging** | Structured `logging` throughout every module. |

---

## 📸 Screenshots

> Coming soon...

---

## 📁 Project Structure

```text
simvox/
├── src/
│   ├── cogs/              # Discord command groups (Music, Playlist, Settings, Stats)
│   ├── core/              # Playback engine & domain logic
│   │   ├── player.py          # Per-guild music state machine
│   │   ├── resolver.py        # URL / search → track list
│   │   ├── scraper.py         # yt-dlp extractor wrapper
│   │   ├── sponsorblock.py    # SponsorBlock segment fetcher
│   │   ├── lyrics.py          # Lyrics lookup & pagination
│   │   ├── recommend.py       # Autoplay recommendations
│   │   ├── idle.py            # Idle-disconnect tracker
│   │   └── permissions.py     # DJ-role permission checks
│   ├── db/                # SQLite layer (schema + repository)
│   │   ├── database.py        # Connection management & schema
│   │   └── repository.py      # Typed CRUD — single source of SQL
│   ├── ui/                # Discord UI Views (buttons, selects, pagination)
│   ├── utils/             # Embed builders & shared helpers
│   ├── assets/            # Static images (logo, icons)
│   └── main.py            # Entry point — bot bootstrap
├── data/                  # Runtime data (SQLite DB lives here)
├── tests/                 # Test scripts
├── requirements.txt       # Pinned Python dependencies
├── .env                   # Environment configuration (not committed)
└── .gitignore
```

| Directory | Responsibility |
|-----------|----------------|
| `src/cogs/` | Discord-facing slash command groups. One cog per feature area. |
| `src/core/` | The playback engine and all domain logic — no Discord UI here. |
| `src/db/` | SQLite schema (`database.py`) and a typed repository (`repository.py`). All SQL lives in one file. |
| `src/ui/` | `discord.ui.View` subclasses — buttons, dropdowns, paginators. |
| `src/utils/` | Embed builders and small pure-function helpers. |
| `src/assets/` | Logo and static imagery. |
| `data/` | Holds `simvox.db`, created automatically on first run. |
| `tests/` | Standalone test and fetch scripts. |

---

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.12 or newer |
| **FFmpeg** | Must be installed and available on your `PATH` |
| **Discord Bot Token** | Create one at the [Discord Developer Portal](https://discord.com/developers/applications) |
| **Internet connection** | Required for audio streaming, search, lyrics, and SponsorBlock |

> **Note:** FFmpeg is what powers audio playback. On Debian/Ubuntu install it with `sudo apt install ffmpeg`; on macOS with `brew install ffmpeg`; on Windows download a build and add it to your `PATH`.

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/tfmvn/simvox.git
cd simvox

# 2. Create a virtual environment
python3.12 -m venv venv

# 3. Activate it
#    Linux / macOS:
source venv/bin/activate
#    Windows (PowerShell):
#    venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure your environment
cp .env.example .env
#    ...then edit .env and paste your Discord bot token

# 6. Run Simvox
python src/main.py
```

Once the bot is online, invite it to your server using the OAuth2 URL generator in the Discord Developer Portal (enable the `applications.commands` and `bot` scopes, plus voice permissions). The slash commands will appear automatically after the first sync.

---

## 🔐 Environment Variables

Simvox reads configuration from a `.env` file at the project root via `python-dotenv`.

| Variable | Required | Description |
|----------|----------|-------------|
| `TOKEN` | ✅ Yes | Your Discord bot token from the Developer Portal. |

```dotenv
# .env
TOKEN=your_discord_bot_token_here
```

> All other configuration — DJ role, volume, idle timeout, quality, SponsorBlock — is managed **in Discord** via the `/settings` commands and stored per-server in SQLite.

---

## 🏃 Running

```bash
# From the project root, with your venv activated:
python src/main.py
```

On startup, Simvox will:

1. Initialize the SQLite database (creating tables if missing).
2. Load all cogs (`music`, `settings`, `playlist`, `stats`).
3. Sync slash commands globally.
4. Restore any saved guild queues and resume playback where possible.

You should see log lines like:

```text
2026-01-01 12:00:00 [INFO] simvox.db: Database ready at .../data/simvox.db
2026-01-01 12:00:00 [INFO] simvox: Loaded extension: cogs.music
2026-01-01 12:00:00 [INFO] simvox: Slash commands synced.
2026-01-01 12:00:00 [INFO] simvox: Online as Simvox#1234 (...)
```

---

## ⚙️ Configuration

All server-level configuration is done **in Discord**, not in files. Every setting below is scoped per-guild and persisted in SQLite.

| Setting | Command | Default | Notes |
|---------|---------|---------|-------|
| **DJ Role** | `/settings djrole [role]` | _none_ | When set, only members with this role can control playback. Clear with no argument. |
| **Default Volume** | `/volume [0–200]` | `100` | Per-guild; clamped to 0–200. |
| **Idle Timeout** | `/settings idletimeout [1–60 min]` | `5 min` (`300s`) | Auto-disconnect after this many minutes of inactivity. |
| **24/7 Mode** | `/247 [enabled]` | _off_ | Keeps the bot in voice permanently, overriding idle disconnect. |
| **Audio Quality** | `/quality [level]` | `high` | `low` · `medium` · `high` (recommended) · `source` (uncapped). |
| **SponsorBlock** | `/settings sponsorblock [enabled]` | _on_ | Auto-skips sponsor segments on supported YouTube tracks. |

Use `/settings view` to inspect the current configuration for your server at any time.

<details>
<summary><strong>🔧 Permission model</strong></summary>

| Action | Required permission |
|--------|---------------------|
| Change DJ role, quality, SponsorBlock, idle timeout, 24/7 | **Manage Server** |
| Skip, remove, move, shuffle, clear, filter, volume | **DJ role** (if set) |
| Play, search, queue, lyrics, stats, settings view | _Anyone in voice_ |

</details>

---

## 💬 Commands

> All commands are Discord **slash commands** — type `/` in a channel Simvox can see to browse them.

### 🎶 Playback

| Command | Description |
|---------|-------------|
| `/play [query]` | Search and play a track (YouTube, SoundCloud, or search). |
| `/playtop [query]` | Add a track to the **top** of the queue. _(DJ)_ |
| `/search [query]` | Browse top results without auto-playing. |
| `/nowplaying` | Show the live now-playing card with controls. |
| `/pause` | Pause playback. |
| `/resume` | Resume playback. |
| `/skip` | Force-skip the current track. _(DJ)_ |
| `/voteskip` | Start a democratic vote to skip. |
| `/replay` | Restart the current track from the beginning. |
| `/seek [mm:ss]` | Seek to a position (e.g. `1:30` or `90`). _(DJ)_ |
| `/volume [0–200]` | Set playback volume. _(DJ)_ |
| `/disconnect` | Disconnect the bot from voice. _(DJ)_ |

### 📋 Queue

| Command | Description |
|---------|-------------|
| `/queue` | Show the paginated queue with ETAs. |
| `/remove [position]` | Remove a track by position (autocomplete). _(DJ)_ |
| `/move [from] [to]` | Reorder a track (autocomplete). _(DJ)_ |
| `/shuffle` | Randomize the queue. _(DJ)_ |
| `/clear` | Wipe the entire queue. _(DJ)_ |
| `/history` | Show the last played tracks. |

### 🎵 Playlists

| Command | Description |
|---------|-------------|
| `/playlist create [name]` | Create a new empty playlist. |
| `/playlist save [name]` | Save the current queue into a playlist. |
| `/playlist load [name]` | Load a playlist into the queue. |
| `/playlist view [name]` | Preview tracks in a playlist. |
| `/playlist list` | List all of your saved playlists. |
| `/playlist delete [name]` | Delete a playlist. |

### ⚙️ Settings & Audio

| Command | Description |
|---------|-------------|
| `/settings view` | Show the current server settings. |
| `/settings djrole [role]` | Set or clear the DJ role. _(Manage Server)_ |
| `/settings sponsorblock [enabled]` | Toggle sponsor-segment auto-skip. _(Manage Server)_ |
| `/settings idletimeout [minutes]` | Set auto-disconnect delay (1–60). _(Manage Server)_ |
| `/247 [enabled]` | Toggle 24/7 voice mode. _(Manage Server)_ |
| `/quality [level]` | Set audio quality tier. _(Manage Server)_ |
| `/loop` | Open the loop-mode picker (Off / Track / Queue). |
| `/filter` | Open the audio-filter picker. _(DJ)_ |
| `/autoplay` | Toggle smart autoplay of recommended tracks. |
| `/lyrics [query]` | Get paginated lyrics for the current or a specified track. |

### 📈 Stats

| Command | Description |
|---------|-------------|
| `/stats` | Show this server's listening statistics. |
| `/help` | Show the in-bot command reference. |

> _(DJ)_ = requires the DJ role if one is set. _(Manage Server)_ = requires server administrator permission.

---

## 🧱 Architecture

Simvox follows a clean, layered design where each module has a single responsibility.

```
┌──────────────────────────────────────────────────────────┐
│                        Discord                           │
│                   (slash commands, voice)                │
└───────────────────────────┬──────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │          cogs/             │  Command handling & UX
              │  music · playlist ·        │  (translate interactions
              │  settings · stats          │   into engine calls)
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │          core/             │  Playback engine & domain
              │  player · resolver ·       │  logic. No Discord UI here.
              │  scraper · sponsorblock ·  │
              │  lyrics · recommend ·      │
              │  idle · permissions        │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │           db/              │  SQLite persistence
              │  database · repository     │  (repository pattern —
              │                            │   all SQL in one file)
              └────────────────────────────┘
```

- **Cogs** (`cogs/`) — Discord-facing command groups. Each cog owns a feature area (`music`, `playlist`, `settings`, `stats`) and translates slash-command interactions into calls on the core engine.
- **Core playback manager** (`core/player.py`) — `GuildMusicManager` is a per-guild state machine handling the queue, loop modes, volume, audio filters, history, autoplay, seek, SponsorBlock segment skipping, quality selection, live progress updates, and SQLite persistence.
- **Repository pattern** (`db/repository.py`) — every database interaction in the entire codebase flows through typed CRUD functions in one file. No raw SQL is written anywhere else, keeping queries auditable and centralized.
- **SQLite persistence** (`db/database.py`) — schema, migrations, and connection management via `aiosqlite` for fully async, event-loop-safe access.
- **Discord UI Views** (`ui/`) — `discord.ui.View` subclasses for search pickers, now-playing controls, queue pagination, filter/loop pickers, vote-skip, and lyrics pagination.
- **Helpers** (`utils/`) — embed builders that give Simvox its consistent look, plus small pure-function helpers (e.g. timestamp parsing).
- **Logging** — structured `logging` throughout every module, so you can always see exactly what the bot is doing.

---

## 📦 Dependencies

Simvox intentionally keeps its dependency surface small.

| Package | Purpose |
|---------|---------|
| [**discord.py**](https://github.com/Rapptz/discord.py) | Discord API client, voice, slash commands, UI views. |
| [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) | Audio extraction from YouTube, SoundCloud, and more. |
| [**aiosqlite**](https://github.com/omnilib/aiosqlite) | Async SQLite access from the bot's event loop. |
| [**aiohttp**](https://github.com/aio-libs/aiohttp) | Async HTTP for external API calls (lyrics, SponsorBlock). |
| [**python-dotenv**](https://github.com/theskumar/python-dotenv) | Loads configuration from `.env`. |
| [**PyNaCl**](https://github.com/pyca/pynacl) | Voice encryption support for discord.py. |

See [`requirements.txt`](requirements.txt) for pinned versions.

---

## 📊 Performance

Simvox is a single-process, single-threaded `asyncio` application backed by SQLite — the lightweight stack means it can run comfortably on a 1-vCPU / 1 GB VPS for a single guild, and scales to many concurrent guilds on modest hardware.

Reasonable expectations:

- **Startup** is near-instant — typically under a second to load all cogs and sync commands.
- **Command latency** is dominated by upstream sources (YouTube / SoundCloud resolution and SponsorBlock lookups), not by Simvox itself.
- **Memory footprint** is small and scales with the number of active guilds and queue sizes.
- **SQLite** easily handles hundreds of thousands of `play_history` rows; indexed lookups remain fast.

> Actual performance depends on your hardware, your network, the number of concurrent voice connections, and Discord's voice server load. The bot is designed to degrade gracefully — a failed external call never takes down playback.

---

## 🤝 Contributing

Contributions are welcome and appreciated! Simvox is community-driven and built in the open.

1. **Fork** the repository and create your branch from `main`.
2. **Discuss** larger changes first by opening an issue — this saves everyone time.
3. **Write clean code** that matches the existing style (see [Development](#️-development)).
4. **Keep commits focused** — one logical change per commit, with a clear message.
5. **Test manually** against a real Discord server before opening a PR.
6. **Open a pull request** describing what changed and why.

Please be respectful and constructive. Reviewers are volunteers.

---

## 🛠️ Development

Simvox uses [Ruff](https://github.com/astral-sh/ruff) for linting and [Black](https://github.com/psf/black) for formatting.

```bash
# Install dev tools
pip install ruff black

# Format the codebase
black src/ tests/

# Lint the codebase
ruff check src/ tests/

# Auto-fix lint issues where possible
ruff check --fix src/ tests/
```

<details>
<summary><strong>Recommended workflow</strong></summary>

```bash
# 1. Create a feature branch
git checkout -b feature/my-new-feature

# 2. Make your changes, then format + lint
black src/ tests/
ruff check --fix src/ tests/

# 3. Run the bot locally to verify
python src/main.py

# 4. Commit and push
git add .
git commit -m "feat: add my new feature"
git push origin feature/my-new-feature

# 5. Open a pull request on GitHub
```

</details>

---

## 🗺️ Roadmap

- [x] Queue system with ETAs
- [x] Playlists (per-user, per-guild)
- [x] Lyrics with pagination
- [x] SponsorBlock auto-skip
- [x] Audio filters (Bass Boost, Nightcore, Vaporwave, 8D, Karaoke, Treble)
- [x] Autoplay with recommendations
- [x] Queue persistence across restarts
- [x] Per-guild statistics
- [x] DJ role & permission model
- [x] 24/7 mode
- [ ] Unit & integration tests
- [ ] CI/CD pipeline
- [ ] Docker support
- [ ] Plugin API for custom cogs

> Have an idea? Open a [discussion](https://github.com/tfmvn/simvox/discussions) or an [issue](https://github.com/tfmvn/simvox/issues).

---

## ❓ FAQ

<details>
<summary><strong>Do I need a database server?</strong></summary>

No. Simvox uses SQLite, which stores everything in a single file at `data/simvox.db`. No PostgreSQL, MySQL, or Redis required.
</details>

<details>
<summary><strong>Does Simvox support Spotify?</strong></summary>

Simvox resolves tracks via `yt-dlp`, so it plays YouTube and SoundCloud sources. Spotify links are not natively supported at this time.
</details>

<details>
<summary><strong>Will my queue survive a restart?</strong></summary>

Yes. Queue state — including the current track, position, loop mode, volume, filter, and autoplay setting — is persisted to SQLite and restored automatically when the bot comes back online.
</details>

<details>
<summary><strong>How do I restrict who can control the bot?</strong></summary>

Use `/settings djrole @Role`. When a DJ role is set, only members with that role can skip, remove, move, shuffle, clear, change volume, and apply filters. Server admins (Manage Server) always retain control.
</details>

<details>
<summary><strong>The bot has no audio — what's wrong?</strong></summary>

The most common cause is **FFmpeg** not being installed or not on your `PATH`. Install it (`sudo apt install ffmpeg` / `brew install ffmpeg` / add to PATH on Windows) and restart the bot.
</details>

<details>
<summary><strong>Is Simvox free to host commercially?</strong></summary>

Yes — Simvox is MIT licensed. You may host, modify, and distribute it freely, including commercially. Attribution is appreciated but not required.
</details>

---

## 📄 License

Simvox is released under the **MIT License**.

```
MIT License

Copyright (c) 2026 tfmvn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See the [LICENSE](LICENSE) file for details.

---

## 💬 Support

- 🐛 **Found a bug?** Open an [issue](https://github.com/tfmvn/simvox/issues) with steps to reproduce it.
- ✨ **Have a feature request?** Start a [discussion](https://github.com/tfmvn/simvox/discussions) or open an issue labeled `enhancement`.
- ❓ **Need help self-hosting?** Check the [FAQ](#-faq) and [Installation](#-installation) sections first, then open a discussion.

When reporting a bug, please include:

1. Simvox version
2. Python version and OS
3. The command you ran and what you expected vs. what happened
4. Relevant log output (with any tokens redacted)

---

## 🙌 Credits

Simvox stands on the shoulders of giants. Thank you to the maintainers and communities behind:

- 🟣 [**discord.py**](https://github.com/Rapptz/discord.py) — the Pythonic Discord API wrapper that powers the entire bot.
- 📺 [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) — the command-line extractor that resolves and fetches audio.
- 🚫 [**SponsorBlock**](https://sponsor.ajay.app/) — the community-driven sponsor-segment database that powers auto-skip.
- 🗄️ [**SQLite**](https://www.sqlite.org/) — the reliable, serverless database that makes zero-config persistence possible.

And to everyone who self-hosts, contributes, and shares Simvox with their communities. 💛

---

<p align="center">
  <strong>Made with ❤️ for the Discord community.</strong>
</p>
<p align="center">
  <a href="https://github.com/tfmvn/simvox">⭐ Star the project</a> ·
  <a href="https://github.com/tfmvn/simvox/fork">🍴 Fork it</a> ·
  <a href="https://github.com/tfmvn/simvox/issues">💬 Get help</a>
</p>
