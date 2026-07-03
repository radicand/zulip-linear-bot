from bot.commands import parse_command, strip_bot_mention
from bot.linear_client import LinearClient


def test_strip_bot_mention() -> None:
    assert strip_bot_mention("@**linear** create test", "linear") == "create test"
    assert strip_bot_mention("@linear find auth", "linear") == "find auth"


def test_parse_command() -> None:
    assert parse_command("help") == ("help", "")
    assert parse_command("AGE-12") == ("get", "AGE-12")
    assert parse_command("create Fix login bug") == ("create", "Fix login bug")
    assert parse_command("find authentication") == ("find", "authentication")
    assert parse_command("some free text") == ("search", "some free text")


def test_parse_identifier() -> None:
    client = LinearClient("key", "team-id", "AGE")
    assert client.parse_identifier("AGE-5") == ("AGE", 5)
    assert client.parse_identifier("age-5") == ("AGE", 5)
