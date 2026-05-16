from src.pycon2026.abstract.event import Event


class ListIssuesEvent(Event):
    name: str = "list_issues"
    issues: list[dict]
