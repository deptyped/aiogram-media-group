from typing import List, Dict

from aiogram import types

from .base import BaseStorage


class MemoryStorage(BaseStorage):
    def __init__(self, data: Dict, prefix: str):
        self._data = data
        self._prefix = prefix

    async def set_media_group_as_handled(self, media_group_id: str) -> bool:
        try:
            _ = self._data[self._prefix][media_group_id]
            return False
        except KeyError:
            self._data.setdefault(self._prefix, {}).setdefault(media_group_id, [])
            return True

    async def append_message_to_media_group(
        self, media_group_id: str, message: types.Message
    ):
        self._data[self._prefix][media_group_id].append(message)

    async def get_media_group_messages(
        self, media_group_id: str
    ) -> List[types.Message]:
        return self._data[self._prefix][media_group_id]

    async def delete_media_group(self, media_group_id: str):
        self._data[self._prefix].pop(media_group_id, None)
