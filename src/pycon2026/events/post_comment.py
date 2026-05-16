from src.pycon2026.abstract.event import Event


class PostCommentEvent(Event):
    name: str = "post_comment"
    issue_number: int
    posted: bool
