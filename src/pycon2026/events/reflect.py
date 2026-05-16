from src.pycon2026.abstract.event import Event


class ReflectEvent(Event):
    reasoning: str
    content: str | None = None
    name: str = "reflect"