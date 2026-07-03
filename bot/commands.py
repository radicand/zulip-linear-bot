from __future__ import annotations

import re
from dataclasses import dataclass

from bot.formatting import HELP_TEXT, format_issue, format_issue_list
from bot.linear_client import LinearClient

IDENTIFIER_RE = re.compile(r"^[A-Za-z]+-\d+$")


@dataclass
class CommandResult:
    content: str


def strip_bot_mention(content: str, bot_name: str) -> str:
    patterns = [
        rf"@\*\*{re.escape(bot_name)}\*\*",
        rf"@{re.escape(bot_name)}",
        rf"@_\*\*[^|]+\|[^\*]+\*\*",
    ]
    cleaned = content
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def parse_command(text: str) -> tuple[str, str]:
    lowered = text.strip()
    if not lowered:
        return "help", ""

    if lowered.lower() in {"help", "commands", "?"}:
        return "help", ""

    if IDENTIFIER_RE.fullmatch(lowered):
        return "get", lowered

    match = re.match(
        r"^(create|find|search|get|update|comment)\s+(.+)$",
        lowered,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).lower(), match.group(2).strip()

    # bare search when user sends free text after mention
    return "search", lowered


def handle_command(client: LinearClient, command: str, args: str) -> CommandResult:
    if command == "help":
        return CommandResult(HELP_TEXT)

    if command in {"find", "search"}:
        issues = client.search_issues(args)
        return CommandResult(format_issue_list(issues))

    if command == "get":
        issue = client.get_issue_by_identifier(args.split()[0])
        return CommandResult(format_issue(issue))

    if command == "create":
        title = args
        description = None
        if "|" in args:
            title, description = [part.strip() for part in args.split("|", 1)]
        issue = client.create_issue(title=title, description=description)
        return CommandResult(f"Created issue:\n\n{format_issue(issue)}")

    if command == "comment":
        identifier, _, body = args.partition(" ")
        if not body:
            raise ValueError("Usage: comment AGE-123 <text>")
        issue = client.get_issue_by_identifier(identifier)
        client.add_comment(issue.id, body)
        return CommandResult(f"Comment added to **{issue.identifier}**.")

    if command == "update":
        match = re.match(
            r"^([A-Za-z]+-\d+)\s+(status|priority|assignee)\s+(.+)$",
            args,
            flags=re.IGNORECASE,
        )
        if not match:
            raise ValueError(
                "Usage: update AGE-123 status <name> | priority <level> | assignee <name>"
            )
        identifier, field, value = match.groups()
        issue = client.get_issue_by_identifier(identifier)
        update_fields: dict[str, object] = {}
        if field.lower() == "status":
            update_fields["stateId"] = client.resolve_state_id(value)
        elif field.lower() == "priority":
            update_fields["priority"] = client.resolve_priority(value)
        elif field.lower() == "assignee":
            update_fields["assigneeId"] = client.resolve_assignee_id(value)
        updated = client.update_issue(issue.id, **update_fields)
        return CommandResult(f"Updated issue:\n\n{format_issue(updated)}")

    raise ValueError(f"Unknown command: {command}")
