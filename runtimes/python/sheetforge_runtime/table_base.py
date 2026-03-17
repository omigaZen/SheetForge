from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Iterator, Optional, TypeVar


T = TypeVar("T")


class TableBase(Generic[T], ABC):
    def __init__(self):
        self._items: dict[int, T] = {}
        self._item_list: list[T] = []
        self._load_time_ms: float = 0.0

    @property
    @abstractmethod
    def table_name(self) -> str:
        raise NotImplementedError

    @property
    def count(self) -> int:
        return len(self._items)

    @property
    def load_time_ms(self) -> float:
        return self._load_time_ms

    def get(self, id: int) -> Optional[T]:
        return self._items.get(id)

    def try_get(self, id: int) -> tuple[bool, Optional[T]]:
        item = self._items.get(id)
        return (item is not None, item)

    def contains(self, id: int) -> bool:
        return id in self._items

    def get_all(self) -> list[T]:
        return self._item_list.copy()

    def __iter__(self) -> Iterator[T]:
        return iter(self._item_list)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, id: int) -> T:
        return self._items[id]

    @abstractmethod
    def load(self, file_path: str) -> None:
        raise NotImplementedError
