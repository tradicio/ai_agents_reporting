from src.pycon2026.abstract.event import Event


class SaveMemoryEvent(Event):
    summary: str
    name: str = "save_memory"
