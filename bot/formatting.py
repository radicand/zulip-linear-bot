from __future__ import annotations

from bot.linear_client import LinearIssue

PRIORITY_LABELS = {
    0: "None",
    1: "Urgent",
    2: "High",
    3: "Medium",
    4: "Low",
}


def format_issue(issue: LinearIssue) -> str:
    assignee = issue.assignee_name or "_unassigned_"
    priority = PRIORITY_LABELS.get(issue.priority, str(issue.priority))
    lines = [
        f"**[{issue.identifier}]({issue.url})** {issue.title}",
        f"Status: **{issue.state_name}** | Priority: **{priority}** | Assignee: **{assignee}**",
    ]
    if issue.description:
        snippet = issue.description.strip()
        if len(snippet) > 400:
            snippet = snippet[:397] + "..."
        lines.append("")
        lines.append(snippet)
    return "\n".join(lines)


def format_issue_list(issues: list[LinearIssue]) -> str:
    if not issues:
        return "No matching issues found."
    return "\n\n".join(format_issue(issue) for issue in issues)


HELP_TEXT = """\
**Linear bot commands**

Mention `@linear` (or DM the bot) with:

- `help` — show this message
- `create <title>` — create an issue (`create Bug | details here`)
- `find <text>` or `search <text>` — search issues
- `get AGE-123` or just `AGE-123` — show one issue
- `update AGE-123 status <name>` — change status
- `update AGE-123 priority <urgent|high|medium|low|none>`
- `update AGE-123 assignee <name>`
- `comment AGE-123 <text>` — add a comment

Inspired by open-source Slack+Linear bots; uses Linear's GraphQL API directly.
"""
