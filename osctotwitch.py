import click
import structlog
import yaml
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from mapper import Mapper
from twitch import TwitchChat, TwitchError


@click.command()
@click.option('--port', '-p', default=1338, type=int, help='Port to listen for OSC messages on (default: 1338)')
@click.option('--config', '-c', 'config_path', default='config.yaml', type=click.Path(exists=True),
              help='Path to YAML config file (default: config.yaml)')
@click.option('--access-token', envvar='TWITCH_ACCESS_TOKEN', required=True,
              help='Twitch user access token with user:write:chat scope [env: TWITCH_ACCESS_TOKEN]')
@click.option('--refresh-token', envvar='TWITCH_REFRESH_TOKEN',
              help='Twitch refresh token, for automatic renewal [env: TWITCH_REFRESH_TOKEN]')
@click.option('--client-id', envvar='TWITCH_CLIENT_ID',
              help='Twitch app client id, needed for refresh [env: TWITCH_CLIENT_ID]')
@click.option('--client-secret', envvar='TWITCH_CLIENT_SECRET',
              help='Twitch app client secret, needed for refresh [env: TWITCH_CLIENT_SECRET]')
def main(port, config_path, access_token, refresh_token, client_id, client_secret):
    """OSC to Twitch Bridge - Receive OSC messages and post them to Twitch chat"""
    logger = structlog.get_logger("osctotwitch")

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    channel = config.get('channel')
    if not channel:
        logger.error("Config is missing 'channel'", config=config_path)
        return
    messages = config.get('messages') or {}

    twitch = TwitchChat(access_token, refresh_token, client_id, client_secret)
    try:
        twitch.validate()
        twitch.get_broadcaster_id(channel)
    except Exception as e:
        logger.error("Failed to authenticate with Twitch",
                     error=str(e), error_type=type(e).__name__)
        return

    dispatcher = Dispatcher()
    mapper = Mapper(twitch, channel, messages)
    dispatcher.set_default_handler(mapper.handle_osc_message)

    try:
        server = BlockingOSCUDPServer(("0.0.0.0", port), dispatcher)
        logger.info("OSC to Twitch bridge running", port=port, channel=channel,
                    sender=twitch.login, configured_addresses=list(messages))
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error("Server error occurred", error=str(e), error_type=type(e).__name__)


if __name__ == '__main__':
    main()
