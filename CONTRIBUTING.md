# Contributing to Simvox

Thanks for taking a look at this. It's a small self-hosted bot, not a huge
project, so the process here is pretty lightweight.

## Before you open a PR

For anything bigger than a bug fix or a typo, open an issue first and
describe what you want to change. Saves both of us the awkward "thanks
but we're going a different direction" conversation after you've already
written the code.

## Setting up

```bash
git clone https://github.com/tfmvn/simvox.git
cd simvox
pip install -r requirements.txt
```

You'll need your own bot token to actually test anything (see the README
for how to get one) — there's no mock/offline mode, so testing means
running the bot against a real Discord server. Make a private test server
if you don't already have one lying around.

## Where things go

- Discord-facing code (slash commands, interaction handling, permission
  checks) goes in `cogs/`.
- Actual logic that doesn't need a `discord.Interaction` goes in `core/`.
- All SQL lives in `db/repository.py`. Don't write raw queries anywhere
  else, even for something that feels like a one-off — repository.py is
  the only place that's supposed to know the schema.
- Embed formatting goes in `utils/embeds.py` so the look stays consistent.
  If you're building a new embed, check there first for something you can
  reuse or copy the style of.

## Code style

- Type hints on new functions, please — the codebase already leans on
  `list[dict]`, `X | None`, etc, so match that instead of `Optional[X]`.
- Docstrings on anything that isn't immediately obvious from the name.
  Doesn't need to be a novel, just enough that someone reading it in 6
  months (probably you) doesn't have to re-derive what it does.
- Keep the DJ-permission pattern consistent: gated commands should start
  with `if not await require_dj(interaction): return`. Don't roll your
  own permission check inside a command unless there's a genuinely
  different rule to enforce.
- Follow whatever formatting the file you're editing already uses.
  There's no enforced formatter/linter right now, so just don't make a
  diff noisier than it needs to be with unrelated reformatting.

## Testing your change

There's no test suite yet, so "testing" means running the bot and
actually using the command in a voice channel:

```bash
python main.py
```

If you touched anything in `db/`, also check what happens on a restart —
a lot of state (queue, playlists, settings) is expected to survive that,
and it's an easy thing to accidentally break.

## Commits and PRs

- One logical change per commit. If your PR is "fix the skip vote bug"
  and also "reformat three unrelated files," split it up.
- Write a commit message that explains *why*, not just what — the diff
  already shows what changed.
- In the PR description, say what you tested and how. "Ran it locally and
  tried X, Y, Z" is enough, we're not expecting a formal test report.

## Reporting bugs

Open an issue with:

- What you ran (the command, roughly what state the queue/bot was in)
- What you expected vs what actually happened
- Python version + OS
- Relevant log output — just redact your token if it's in there

## Anything else

If you're not sure whether something fits the project or you just want to
sanity-check an approach before writing code, open an issue and ask. Way
better than finding out after the fact that the direction doesn't fit.
