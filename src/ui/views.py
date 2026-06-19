"""
ui/views.py
All discord.ui Views, Selects and Buttons used by Simvox.
"""
import discord
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.player import GuildMusicManager
    from discord.ext import commands


# ── Search Dropdown ──────────────────────────────────────────────────────────

class TrackSelect(discord.ui.Select):
    def __init__(self, tracks: list, cog):
        self.tracks = tracks
        self.cog    = cog
        opts = []
        for i, t in enumerate(tracks[:25]):
            from utils.embeds import _fmt_time
            label = t["title"][:90] if len(t["title"]) > 90 else t["title"]
            dur   = _fmt_time(t.get("duration", 0))
            opts.append(discord.SelectOption(
                label=f"{i+1}. {label}",
                value=str(i),
                description=f"{t.get('uploader','?')} • {dur}",
                emoji="🎵",
            ))
        super().__init__(
            placeholder="🎵  Choose a track…",
            min_values=1, max_values=1,
            options=opts,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        track = self.tracks[int(self.values[0])]

        manager = await self.cog.ensure_voice(interaction)
        if not manager:
            return

        manager.add_to_queue(track)
        self.disabled = True
        await interaction.edit_original_response(view=self.view)

        pos = len(manager.queue)
        if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
            await manager.play_next()
            from utils.embeds import now_playing
            from ui.views import NowPlayingView
            embed = now_playing(track, 0, interaction.user)
            view  = NowPlayingView(manager)
            msg   = await interaction.followup.send(embed=embed, view=view)
            manager.np_message   = msg
            manager.text_channel = interaction.channel
        else:
            from utils.embeds import track_added
            await interaction.followup.send(embed=track_added(track, pos))


class SearchView(discord.ui.View):
    def __init__(self, tracks: list, cog):
        super().__init__(timeout=60)
        self.add_item(TrackSelect(tracks, cog))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ── Now Playing Controls ─────────────────────────────────────────────────────

class NowPlayingView(discord.ui.View):
    def __init__(self, manager: "GuildMusicManager"):
        super().__init__(timeout=None)
        self.manager = manager
        self._update_loop_label()

    def _update_loop_label(self):
        for item in self.children:
            if getattr(item, "custom_id", None) == "loop_btn":
                icons = {"off": "🔁", "track": "🔂", "queue": "🔁"}
                item.emoji = discord.PartialEmoji(name=icons.get(self.manager.loop_mode, "🔁"))

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary, row=0)
    async def replay_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.manager.replay()
        await interaction.followup.send("⏮ Replaying from start.", ephemeral=True, delete_after=5)

    @discord.ui.button(emoji="⏸", style=discord.ButtonStyle.primary, row=0)
    async def pause_resume_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.manager.voice_client and self.manager.voice_client.is_playing():
            self.manager.pause()
            button.emoji = discord.PartialEmoji(name="▶")
            button.style = discord.ButtonStyle.success
        else:
            self.manager.resume()
            button.emoji = discord.PartialEmoji(name="⏸")
            button.style = discord.ButtonStyle.primary
        await interaction.edit_original_response(view=self)

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.manager.skip()
        await interaction.followup.send("⏭ Skipped.", ephemeral=True, delete_after=5)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=0, custom_id="loop_btn")
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        modes = ["off", "track", "queue"]
        idx   = modes.index(self.manager.loop_mode)
        self.manager.loop_mode = modes[(idx + 1) % len(modes)]
        labels = {"off": "Loop: Off", "track": "Loop: Track 🔂", "queue": "Loop: Queue 🔁"}
        await interaction.followup.send(f"🔁 {labels[self.manager.loop_mode]}", ephemeral=True, delete_after=5)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.manager.shuffle()
        await interaction.followup.send("🔀 Queue shuffled.", ephemeral=True, delete_after=5)

    @discord.ui.button(label="Queue", emoji="📋", style=discord.ButtonStyle.secondary, row=1)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.embeds import queue_embed
        from ui.views    import QueueView
        embed = queue_embed(self.manager, 0)
        view  = QueueView(self.manager, 0)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Filter", emoji="🎛", style=discord.ButtonStyle.secondary, row=1)
    async def filter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = FilterView(self.manager)
        from utils.embeds import filters_embed
        await interaction.response.send_message(
            embed=filters_embed(self.manager.active_filter), view=view, ephemeral=True
        )

    @discord.ui.button(label="Vol –", emoji="🔉", style=discord.ButtonStyle.danger, row=1)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.manager.set_volume(self.manager.volume - 10)
        from utils.embeds import volume_embed
        await interaction.followup.send(embed=volume_embed(self.manager.volume), ephemeral=True, delete_after=5)

    @discord.ui.button(label="Vol +", emoji="🔊", style=discord.ButtonStyle.success, row=1)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.manager.set_volume(self.manager.volume + 10)
        from utils.embeds import volume_embed
        await interaction.followup.send(embed=volume_embed(self.manager.volume), ephemeral=True, delete_after=5)


# ── Queue Paginator ──────────────────────────────────────────────────────────

class QueueView(discord.ui.View):
    def __init__(self, manager: "GuildMusicManager", page: int = 0):
        super().__init__(timeout=120)
        self.manager = manager
        self.page    = page
        self._refresh_buttons()

    def _refresh_buttons(self):
        total = len(self.manager.queue)
        max_page = max(0, (total - 1) // 10)
        for item in self.children:
            if getattr(item, "custom_id", None) == "prev_page":
                item.disabled = self.page <= 0
            if getattr(item, "custom_id", None) == "next_page":
                item.disabled = self.page >= max_page

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, custom_id="prev_page")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._refresh_buttons()
        from utils.embeds import queue_embed
        await interaction.response.edit_message(embed=queue_embed(self.manager, self.page), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, custom_id="next_page")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        max_page = max(0, (len(self.manager.queue) - 1) // 10)
        self.page = min(max_page, self.page + 1)
        self._refresh_buttons()
        from utils.embeds import queue_embed
        await interaction.response.edit_message(embed=queue_embed(self.manager, self.page), view=self)

    @discord.ui.button(label="🔀 Shuffle", style=discord.ButtonStyle.primary)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.manager.shuffle()
        from utils.embeds import queue_embed
        await interaction.response.edit_message(embed=queue_embed(self.manager, self.page), view=self)

    @discord.ui.button(label="🗑 Clear", style=discord.ButtonStyle.danger)
    async def clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.manager.clear_queue()
        from utils.embeds import queue_embed
        await interaction.response.edit_message(embed=queue_embed(self.manager, 0), view=self)


# ── Audio Filter Select ───────────────────────────────────────────────────────

class FilterSelect(discord.ui.Select):
    FILTERS = [
        ("none",      "Off",         "No processing", "🎵"),
        ("bassboost", "Bass Boost",  "Heavy low-end",  "🔊"),
        ("nightcore", "Nightcore",   "Fast & pitched up", "⚡"),
        ("vaporwave", "Vaporwave",   "Slow & dreamy",  "🌊"),
        ("8d",        "8D Audio",    "Rotating stereo", "🎧"),
        ("karaoke",   "Karaoke",     "Vocal removal",  "🎤"),
        ("treble",    "Treble Boost","Crispy highs",   "✨"),
    ]

    def __init__(self, manager: "GuildMusicManager"):
        self.manager = manager
        opts = [
            discord.SelectOption(
                label=label, value=key, description=desc, emoji=emoji,
                default=(key == manager.active_filter),
            )
            for key, label, desc, emoji in self.FILTERS
        ]
        super().__init__(placeholder="Choose a filter…", options=opts)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.manager.apply_filter(self.values[0])
        from utils.embeds import filters_embed
        await interaction.edit_original_response(
            embed=filters_embed(self.manager.active_filter)
        )
        await interaction.followup.send(
            f"🎛 Filter set to **{self.values[0]}**.", ephemeral=True, delete_after=5
        )


class FilterView(discord.ui.View):
    def __init__(self, manager: "GuildMusicManager"):
        super().__init__(timeout=60)
        self.add_item(FilterSelect(manager))


# ── Loop Mode Select ─────────────────────────────────────────────────────────

class LoopSelect(discord.ui.Select):
    def __init__(self, manager: "GuildMusicManager"):
        self.manager = manager
        opts = [
            discord.SelectOption(label="Off",       value="off",   emoji="➡", default=manager.loop_mode=="off"),
            discord.SelectOption(label="Loop Track", value="track", emoji="🔂", default=manager.loop_mode=="track"),
            discord.SelectOption(label="Loop Queue", value="queue", emoji="🔁", default=manager.loop_mode=="queue"),
        ]
        super().__init__(placeholder="Loop mode…", options=opts)

    async def callback(self, interaction: discord.Interaction):
        self.manager.set_loop(self.values[0])
        await interaction.response.send_message(
            f"Loop set to **{self.values[0]}**.", ephemeral=True, delete_after=5
        )


class LoopView(discord.ui.View):
    def __init__(self, manager: "GuildMusicManager"):
        super().__init__(timeout=30)
        self.add_item(LoopSelect(manager))


# ── Vote Skip ────────────────────────────────────────────────────────────────

class VoteSkipView(discord.ui.View):
    def __init__(self, manager: "GuildMusicManager", required: int):
        super().__init__(timeout=30)
        self.manager  = manager
        self.required = required

    @discord.ui.button(label="Skip (0)", emoji="⏭", style=discord.ButtonStyle.danger)
    async def vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.manager.skip_votes:
            await interaction.response.send_message("You already voted.", ephemeral=True, delete_after=5)
            return
        self.manager.skip_votes.add(uid)
        count = len(self.manager.skip_votes)
        button.label = f"Skip ({count}/{self.required})"
        if count >= self.required:
            self.manager.skip()
            self.stop()
            await interaction.response.edit_message(content="⏭ Vote passed — skipped!", view=None)
        else:
            await interaction.response.edit_message(view=self)

