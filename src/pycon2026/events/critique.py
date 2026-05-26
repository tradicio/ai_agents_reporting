from src.pycon2026.abstract.event import Event


class CritiqueEvent(Event):
    content: str
    name: str = "critique"
