from abc import abstractmethod, ABC
from typing import List

from aiogram import types


class BaseStorage(ABC):
    @abstractmethod
    async def set_media_group_as_handled(self, media_group_id: str) -> bool:
        pass

    @abstractmethod
    async def append_message_to_media_group(
        self, media_group_id: str, message: types.Message
    ):
        pass

    @abstractmethod
    async def get_media_group_messages(
        self, media_group_id: str
    ) -> List[types.Message]:
        pass

    @abstractmethod
    async def delete_media_group(self, media_group_id: str):
        pass
