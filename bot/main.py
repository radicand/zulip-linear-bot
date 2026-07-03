from __future__ import annotations

import logging
import sys
import time

import zulip

from bot.commands import CommandResult, handle_command, parse_command, strip_bot_mention
from bot.config import load_settings
from bot.linear_client import LinearClient

logger = logging.getLogger(__name__)


def should_handle_message(message: dict, bot_email: str) -> bool:
    if message.get("sender_email") == bot_email:
        return False
    if message.get("type") == "private":
        return True
    content = message.get("content", "").lower()
    return (
        "@linear" in content
        or "**linear**" in content
        or "linear|" in content
        or "user-mention" in content and "linear" in content
    )


def build_reply(message: dict, result: CommandResult) -> dict:
    if message.get("type") == "stream":
        return {
            "type": "stream",
            "to": message["display_recipient"],
            "subject": message["subject"],
            "content": result.content,
        }
    return {
        "type": "private",
        "to": message["sender_email"],
        "content": result.content,
    }


def main() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    zulip_client = zulip.Client(
        email=settings.zulip_email,
        api_key=settings.zulip_api_key,
        site=settings.zulip_site,
    )
    linear_client = LinearClient(
        api_key=settings.linear_api_key,
        team_id=settings.linear_team_id,
        team_key=settings.linear_team_key,
    )

    logger.info("Starting Zulip Linear bot on %s", settings.zulip_site)

    def handle_message(message: dict) -> None:
        logger.info(
            "Received message %s from %s in %s: %s",
            message.get("id"),
            message.get("sender_email"),
            message.get("display_recipient") or "dm",
            message.get("content", "")[:160],
        )
        if not should_handle_message(message, settings.zulip_email):
            logger.info("Ignoring message %s (no bot mention)", message.get("id"))
            return

        raw = strip_bot_mention(message.get("content", ""), settings.zulip_bot_name)
        logger.info("Handling command from %s: %s", message.get("sender_email"), raw[:120])
        try:
            command, args = parse_command(raw)
            result = handle_command(linear_client, command, args)
        except Exception as exc:  # noqa: BLE001 - user-facing bot errors
            logger.exception("Command failed")
            result = CommandResult(f":warning: {exc}")

        response = zulip_client.send_message(build_reply(message, result))
        if response.get("result") != "success":
            logger.error("Failed to send Zulip reply: %s", response)

    while True:
        try:
            zulip_client.call_on_each_message(handle_message)
        except Exception:
            logger.exception("Bot loop crashed; restarting in 5 seconds")
            time.sleep(5)


if __name__ == "__main__":
    main()
