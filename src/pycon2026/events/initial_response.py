from src.pycon2026.abstract.event import Event


class InitialResponseEvent(Event):
    content: str
    name: str = "initial_response"
