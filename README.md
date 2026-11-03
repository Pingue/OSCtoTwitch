# OSCtoTwitch

OSC to Twitch chat bridge. Listens for OSC messages and posts them to the
chat of one Twitch channel, defined in a config file. Sister project to
[OSCtoAtem](https://github.com/Pingue/OSCtoAtem).

## Setup

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml   # set `channel` and any named messages
```

### Twitch credentials

You need a Twitch **user access token** with the `user:write:chat` scope
(messages are sent as the user who owns the token — a dedicated bot account
works well). Supply it via `--access-token` or the environment:

| Env var | Required | Purpose |
|---|---|---|
| `TWITCH_ACCESS_TOKEN` | yes | User access token (`user:write:chat`) |
| `TWITCH_REFRESH_TOKEN` | no | Enables automatic token refresh |
| `TWITCH_CLIENT_ID` | no* | App client id (*needed for refresh) |
| `TWITCH_CLIENT_SECRET` | no* | App client secret (*needed for refresh) |

## Run

```bash
TWITCH_ACCESS_TOKEN=xxxx python osctotwitch.py --port 1338 --config config.yaml
```

## OSC messages

- `/twitch/say <args...>` — sends the arguments, space-joined, to chat.
- Any address under `messages:` in the config — sends that template, with
  `{0}`, `{1}`, … replaced by the OSC arguments.

Messages are capped at 500 characters (Twitch's limit).

## Tests

```bash
pip install pytest && pytest
```
