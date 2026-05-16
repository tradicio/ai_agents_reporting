from src.pycon2026.abstract.event import Event

class AnswerEvent(Event):
    name: str = "answer"
    content: str