"""Minimal Twitch chat client using the Helix "Send Chat Message" API."""
from typing import Optional
import requests
import structlog

HELIX_URL = "https://api.twitch.tv/helix"
OAUTH_URL = "https://id.twitch.tv/oauth2"
MAX_MESSAGE_LENGTH = 500
REQUIRED_SCOPE = "user:write:chat"


class TwitchError(Exception):
    """Raised when talking to Twitch fails."""


class TwitchChat:
    """Sends chat messages as the user that owns the supplied access token.

    Needs a *user* access token with the ``user:write:chat`` scope. If a
    refresh token, client id and client secret are also supplied, an expired
    token is refreshed automatically.
    """

    def __init__(self, access_token: str, refresh_token: Optional[str] = None,
                 client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 timeout: float = 10.0, session: Optional[requests.Session] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.session = session or requests.Session()
        self.user_id: Optional[str] = None
        self.login: Optional[str] = None
        self.logger = structlog.get_logger("twitch")
        self._broadcaster_ids = {}

    def validate(self) -> None:
        """Validate the token, learning the client id and sender user id."""
        resp = self.session.get(f"{OAUTH_URL}/validate",
                                headers={"Authorization": f"OAuth {self.access_token}"},
                                timeout=self.timeout)
        if resp.status_code == 401 and self._refresh():
            return self.validate()
        if resp.status_code != 200:
            raise TwitchError(f"Token validation failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        if REQUIRED_SCOPE not in data.get("scopes", []):
            raise TwitchError(f"Access token is missing the '{REQUIRED_SCOPE}' scope")
        self.client_id = data["client_id"]
        self.user_id = data["user_id"]
        self.login = data.get("login")
        self.logger.info("Twitch token validated", login=self.login, user_id=self.user_id)

    def _refresh(self) -> bool:
        if not (self.refresh_token and self.client_id and self.client_secret):
            return False
        resp = self.session.post(f"{OAUTH_URL}/token", data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }, timeout=self.timeout)
        if resp.status_code != 200:
            self.logger.error("Token refresh failed", status=resp.status_code, body=resp.text)
            return False
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.logger.info("Twitch access token refreshed")
        return True

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}", "Client-Id": self.client_id or ""}

    def _helix(self, method: str, path: str, **kwargs) -> requests.Response:
        resp = self.session.request(method, f"{HELIX_URL}{path}", headers=self._headers(),
                                    timeout=self.timeout, **kwargs)
        if resp.status_code == 401 and self._refresh():
            resp = self.session.request(method, f"{HELIX_URL}{path}", headers=self._headers(),
                                        timeout=self.timeout, **kwargs)
        return resp

    def get_broadcaster_id(self, channel: str) -> str:
        channel = channel.lstrip("#").lower()
        if channel not in self._broadcaster_ids:
            resp = self._helix("GET", "/users", params={"login": channel})
            if resp.status_code != 200 or not resp.json().get("data"):
                raise TwitchError(f"Could not find Twitch channel '{channel}' ({resp.status_code})")
            self._broadcaster_ids[channel] = resp.json()["data"][0]["id"]
        return self._broadcaster_ids[channel]

    def send_message(self, channel: str, message: str) -> None:
        """Send ``message`` to ``channel``'s chat."""
        if self.user_id is None:
            self.validate()
        message = message.strip()
        if not message:
            raise TwitchError("Refusing to send an empty message")
        if len(message) > MAX_MESSAGE_LENGTH:
            self.logger.warning("Message truncated", length=len(message))
            message = message[:MAX_MESSAGE_LENGTH]
        resp = self._helix("POST", "/chat/messages", json={
            "broadcaster_id": self.get_broadcaster_id(channel),
            "sender_id": self.user_id,
            "message": message,
        })
        if resp.status_code != 200:
            raise TwitchError(f"Send failed ({resp.status_code}): {resp.text}")
        result = (resp.json().get("data") or [{}])[0]
        if not result.get("is_sent", False):
            raise TwitchError(f"Twitch dropped the message: {result.get('drop_reason')}")
        self.logger.info("Chat message sent", channel=channel, message=message)
