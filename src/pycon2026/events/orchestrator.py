from src.pycon2026.abstract.event import Event


class DelegateDevEvent(Event):
    name: str = "delegate_dev"
    task_summary: str


class DelegateTesterEvent(Event):
    name: str = "delegate_tester"
    task_summary: str


class DelegateDocEvent(Event):
    name: str = "delegate_doc"
    task_summary: str


class WriteFileEvent(Event):
    name: str = "write_file"
    path: str


class OrchestratorDoneEvent(Event):
    name: str = "orchestrator_done"
    files_written: list[str]
