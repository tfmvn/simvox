"""
utils/queue.py
A simple per-guild queue of upcoming tracks, kept separate from the
music cog so the command logic doesn't have to manage queue dicts itself.
"""
from dataclasses import dataclass


@dataclass
class Track:
    url: str
    title: str


class QueueManager:
    """Keeps one queue of Tracks per guild."""

    def __init__(self):
        self._queues: dict[int, list[Track]] = {}

    def get(self, guild_id: int) -> list[Track]:
        """Returns the queue for a guild, creating an empty one if needed."""
        return self._queues.setdefault(guild_id, [])

    def add(self, guild_id: int, url: str, title: str) -> None:
        self.get(guild_id).append(Track(url=url, title=title))

    def pop_next(self, guild_id: int) -> Track | None:
        """Removes and returns the next track, or None if the queue is empty."""
        queue = self.get(guild_id)
        return queue.pop(0) if queue else None

    def remove(self, guild_id: int, index: int) -> Track | None:
        """Removes the track at the given 1-based index, or None if invalid."""
        queue = self.get(guild_id)
        if index < 1 or index > len(queue):
            return None
        return queue.pop(index - 1)

    def clear(self, guild_id: int) -> None:
        self.get(guild_id).clear()