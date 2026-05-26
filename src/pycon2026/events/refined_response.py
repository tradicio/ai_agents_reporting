from src.pycon2026.abstract.event import Event


class RefinedResponseEvent(Event):
    content: str
    name: str = "refined_response"
