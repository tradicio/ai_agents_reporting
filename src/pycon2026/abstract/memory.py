class Memory:

    def __init__(self):
        self._store: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        self._store[key] = value

    def get(self, key: str, default: object = None) -> object:
        return self._store.get(key, default)

    def clear(self) -> None:
        self._store.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __repr__(self) -> str:
        return f"Memory({self._store!r})"
