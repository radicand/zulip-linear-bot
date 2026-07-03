from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

LINEAR_API_URL = "https://api.linear.app/graphql"

PRIORITY_BY_NAME = {
    "none": 0,
    "urgent": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
}


@dataclass
class LinearIssue:
    id: str
    identifier: str
    title: str
    description: str | None
    url: str
    priority: int
    state_name: str
    assignee_name: str | None

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> LinearIssue:
        assignee = node.get("assignee") or {}
        state = node.get("state") or {}
        return cls(
            id=node["id"],
            identifier=node["identifier"],
            title=node["title"],
            description=node.get("description"),
            url=node["url"],
            priority=node.get("priority", 0),
            state_name=state.get("name", "Unknown"),
            assignee_name=assignee.get("displayName") or assignee.get("name"),
        )


class LinearClient:
    def __init__(self, api_key: str, team_id: str, team_key: str = "") -> None:
        self.api_key = api_key
        self.team_id = team_id
        self.team_key = team_key.upper()

    def _request(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        response = httpx.post(
            LINEAR_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": self.api_key,
            },
            json={"query": query, "variables": variables or {}},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"][0].get("message", "Linear API error"))
        return payload["data"]

    def parse_identifier(self, raw: str) -> tuple[str, int] | None:
        value = raw.strip().upper()
        if self.team_key:
            match = re.fullmatch(rf"{re.escape(self.team_key)}-(\d+)", value)
            if match:
                return self.team_key, int(match.group(1))
        match = re.fullmatch(r"([A-Z]+)-(\d+)", value)
        if match:
            return match.group(1), int(match.group(2))
        return None

    def get_issue_by_identifier(self, identifier: str) -> LinearIssue:
        parsed = self.parse_identifier(identifier)
        if not parsed:
            raise ValueError(f"Invalid issue identifier: {identifier}")
        team_key, number = parsed
        data = self._request(
            """
            query IssueByIdentifier($filter: IssueFilter!) {
              issues(filter: $filter, first: 1) {
                nodes {
                  id identifier title description url priority
                  state { name }
                  assignee { id name displayName }
                }
              }
            }
            """,
            {
                "filter": {
                    "team": {"key": {"eq": team_key}},
                    "number": {"eq": number},
                }
            },
        )
        nodes = data["issues"]["nodes"]
        if not nodes:
            raise ValueError(f"Issue not found: {identifier}")
        return LinearIssue.from_node(nodes[0])

    def search_issues(self, query: str, limit: int = 10) -> list[LinearIssue]:
        data = self._request(
            """
            query SearchIssues($filter: IssueFilter!, $first: Int!) {
              issues(filter: $filter, first: $first, orderBy: updatedAt) {
                nodes {
                  id identifier title description url priority
                  state { name }
                  assignee { id name displayName }
                }
              }
            }
            """,
            {
                "first": limit,
                "filter": {
                    "team": {"id": {"eq": self.team_id}},
                    "or": [
                        {"title": {"containsIgnoreCase": query}},
                        {"description": {"containsIgnoreCase": query}},
                    ],
                },
            },
        )
        return [LinearIssue.from_node(node) for node in data["issues"]["nodes"]]

    def create_issue(
        self,
        title: str,
        description: str | None = None,
        priority: int | None = None,
        assignee_id: str | None = None,
        state_id: str | None = None,
    ) -> LinearIssue:
        issue_input: dict[str, Any] = {
            "teamId": self.team_id,
            "title": title,
        }
        if description:
            issue_input["description"] = description
        if priority is not None:
            issue_input["priority"] = priority
        if assignee_id:
            issue_input["assigneeId"] = assignee_id
        if state_id:
            issue_input["stateId"] = state_id

        data = self._request(
            """
            mutation CreateIssue($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success
                issue {
                  id identifier title description url priority
                  state { name }
                  assignee { id name displayName }
                }
              }
            }
            """,
            {"input": issue_input},
        )
        result = data["issueCreate"]
        if not result.get("success"):
            raise RuntimeError("Failed to create issue")
        return LinearIssue.from_node(result["issue"])

    def update_issue(self, issue_id: str, **fields: Any) -> LinearIssue:
        data = self._request(
            """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
              issueUpdate(id: $id, input: $input) {
                success
                issue {
                  id identifier title description url priority
                  state { name }
                  assignee { id name displayName }
                }
              }
            }
            """,
            {"id": issue_id, "input": fields},
        )
        result = data["issueUpdate"]
        if not result.get("success"):
            raise RuntimeError("Failed to update issue")
        return LinearIssue.from_node(result["issue"])

    def add_comment(self, issue_id: str, body: str) -> None:
        data = self._request(
            """
            mutation CreateComment($input: CommentCreateInput!) {
              commentCreate(input: $input) {
                success
              }
            }
            """,
            {"input": {"issueId": issue_id, "body": body}},
        )
        if not data["commentCreate"].get("success"):
            raise RuntimeError("Failed to add comment")

    def list_workflow_states(self) -> list[dict[str, str]]:
        data = self._request(
            """
            query WorkflowStates($filter: WorkflowStateFilter!) {
              workflowStates(filter: $filter) {
                nodes { id name }
              }
            }
            """,
            {"filter": {"team": {"id": {"eq": self.team_id}}}},
        )
        return data["workflowStates"]["nodes"]

    def list_team_members(self) -> list[dict[str, str]]:
        data = self._request(
            """
            query TeamMembers($teamId: String!) {
              team(id: $teamId) {
                members {
                  nodes { id name displayName email }
                }
              }
            }
            """,
            {"teamId": self.team_id},
        )
        return data["team"]["members"]["nodes"]

    def resolve_state_id(self, name: str) -> str:
        target = name.strip().lower()
        for state in self.list_workflow_states():
            if state["name"].lower() == target:
                return state["id"]
        raise ValueError(f"Unknown status: {name}")

    def resolve_assignee_id(self, name: str) -> str:
        target = name.strip().lower()
        for member in self.list_team_members():
            candidates = [
                member.get("displayName", ""),
                member.get("name", ""),
                member.get("email", ""),
            ]
            if any(target == value.lower() for value in candidates if value):
                return member["id"]
            if any(target in value.lower() for value in candidates if value):
                return member["id"]
        raise ValueError(f"Unknown assignee: {name}")

    @staticmethod
    def resolve_priority(name: str) -> int:
        value = PRIORITY_BY_NAME.get(name.strip().lower())
        if value is None:
            raise ValueError(f"Unknown priority: {name}")
        return value
