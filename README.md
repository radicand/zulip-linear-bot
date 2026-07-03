# Zulip Linear Bot

Interactive [Zulip](https://zulip.com) bot for [Linear](https://linear.app) issue management.

Linear's official `@Linear` Slack integration is proprietary. This bot models the same workflows using open-source patterns from community Slack+Linear projects (notably [Harper](https://github.com/DahaoTang/Harper)) and talks to Linear's GraphQL API directly.

## Features

- Create, search, view, update, and comment on Linear issues from Zulip
- Responds to `@linear` mentions in channels and direct messages
- Deterministic command parsing (no LLM required)

## Commands

```
@linear help
@linear create Fix login bug
@linear create Bug title | optional description
@linear find authentication
@linear AGE-123
@linear update AGE-123 status "In Progress"
@linear update AGE-123 priority high
@linear update AGE-123 assignee alice
@linear comment AGE-123 Looks like a TLS issue
```

## Configuration

| Variable | Description |
|----------|-------------|
| `ZULIP_EMAIL` | Bot account email |
| `ZULIP_API_KEY` | Bot API key |
| `ZULIP_SITE` | Zulip server URL |
| `ZULIP_BOT_NAME` | Bot mention name (default: `linear`) |
| `LINEAR_API_KEY` | Linear personal API key |
| `LINEAR_TEAM_ID` | Default Linear team UUID |
| `LINEAR_TEAM_KEY` | Team key prefix for identifiers (e.g. `AGE`) |

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export ZULIP_EMAIL=...
export ZULIP_API_KEY=...
export ZULIP_SITE=...
export LINEAR_API_KEY=...
export LINEAR_TEAM_ID=...
export LINEAR_TEAM_KEY=AGE
zulip-linear-bot
```

## Docker

```bash
docker build -t zulip-linear-bot .
docker run --rm -e ZULIP_EMAIL=... -e ZULIP_API_KEY=... -e ZULIP_SITE=... \
  -e LINEAR_API_KEY=... -e LINEAR_TEAM_ID=... -e LINEAR_TEAM_KEY=AGE zulip-linear-bot
```

## License

MIT
