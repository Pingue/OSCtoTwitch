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

### Getting a token

1. Log in to Twitch **as the account that should post** (e.g. a bot account).
2. Register an app at <https://dev.twitch.tv/console/apps> → *Register Your Application*:
   - OAuth Redirect URL: `http://localhost:3000`
   - Category: *Chat Bot* (or similar); Client Type: **Confidential**
   - Note the **Client ID**, and generate a **Client Secret**.
3. Install the [Twitch CLI](https://dev.twitch.tv/docs/cli/):

   ```bash
   # macOS / Linux (Homebrew)
   brew install twitchdev/twitch/twitch-cli
   ```

   ```powershell
   # Windows (Scoop)
   scoop bucket add twitch https://github.com/twitchdev/scoop-bucket.git
   scoop install twitch-cli
   ```

   Otherwise download a binary from the
   [releases page](https://github.com/twitchdev/twitch-cli/releases) and put it on your `PATH`.
   Then generate a user token:

   ```bash
   twitch configure                      # paste the Client ID and Secret
   twitch token -u -s 'user:write:chat'  # opens a browser; approve as the posting account
   ```

   It prints an **access token** and a **refresh token**.
4. Export them (the client id/secret and refresh token let the bridge renew
   the access token itself, which otherwise expires after a few hours):

   ```bash
   export TWITCH_ACCESS_TOKEN=...
   export TWITCH_REFRESH_TOKEN=...
   export TWITCH_CLIENT_ID=...
   export TWITCH_CLIENT_SECRET=...
   ```

Without the Twitch CLI, you can open
`https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=<CLIENT_ID>&redirect_uri=http://localhost:3000&scope=user:write:chat`
in a browser, approve, then exchange the `code` from the redirect URL with a
POST to `https://id.twitch.tv/oauth2/token` (`client_id`, `client_secret`,
`code`, `grant_type=authorization_code`, `redirect_uri`).

Alternatively, put them in a `.env` file next to the script (see
`.env.example`; `.env` is gitignored). It's optional, and real environment
variables and command-line options take precedence over it.

Keep these values secret; anyone with them can chat as that account.

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
