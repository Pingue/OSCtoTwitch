from typing import Any, Dict, List
import structlog

from twitch import TwitchChat, TwitchError

SAY_ADDRESS = "/twitch/say"


class Mapper:
    """Maps OSC messages to Twitch chat messages for one configured channel."""

    def __init__(self, twitch: TwitchChat, channel: str, messages: Dict[str, str] = None):
        self.twitch = twitch
        self.channel = channel
        self.messages = messages or {}
        self.logger = structlog.get_logger("mapper")

    def build_message(self, address: str, args: List[Any]) -> str:
        """Work out the chat text for an OSC message, or '' if the address is unknown."""
        if address in self.messages:
            template = self.messages[address]
            try:
                return template.format(*args)
            except IndexError:
                self.logger.error("Not enough OSC arguments for template",
                                  address=address, template=template, args=args)
                return ""
        if address == SAY_ADDRESS:
            return " ".join(str(a) for a in args)
        return ""

    def handle_osc_message(self, address: str, *args: Any) -> None:
        self.logger.info("OSC message received", address=address, args=args)
        text = self.build_message(address, list(args))
        if not text.strip():
            self.logger.warning("No chat message produced for OSC message", address=address)
            return
        try:
            self.twitch.send_message(self.channel, text)
        except Exception as e:
            self.logger.error("Failed to send chat message", address=address,
                              error=str(e), error_type=type(e).__name__)
