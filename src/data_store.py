from typing import Any


class DataStore:
    def __init__(self):
        self.data = {}

    def get(self, key) -> Any:
        return self.data.get(key)

    def set(self, key: str, value: Any):
        self.data[key] = value
