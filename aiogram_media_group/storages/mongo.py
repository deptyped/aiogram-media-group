from typing import List
from typing import TYPE_CHECKING

from aiogram import types

from aiogram_media_group.storages.base import BaseStorage

if TYPE_CHECKING:
    from motor import motor_asyncio

try:
    import ujson as json
except ImportError:
    import json


class MongoStorage(BaseStorage):
    @classmethod
    async def init(cls, db: "motor_asyncio.AsyncIOMotorDatabase") -> "MongoStorage":
        '''
        Gets aiogram_fsm database, in which creates aiogram_media_group collection

        '''    
        self = MongoStorage()
        
        try:
            if not "aiogram_media_group" in await db.list_collection_names():
                await db.create_collection("aiogram_media_group")
        except:
            # ignore multiple calls to mongo at the same time
            pass
        
        self._collection = db.aiogram_media_group

        return self

    async def set_media_group_as_handled(self, media_group_id: str) -> bool:
        try:
            if await self._collection.find_one({"_id": media_group_id}) is None:
                return await self._collection.insert_one({"_id": media_group_id, "messages": []})
        except:
            # ignore multiple calls to mongo at the same time
            return False
        finally:
            return False

    async def append_message_to_media_group(self, media_group_id: str, message: types.Message):
        await self._collection.update_one({"_id": media_group_id}, {"$push": {"messages": json.dumps(message.to_python())}})

    async def get_media_group_messages(self, media_group_id: str) -> List[types.Message]:
        raw_messages = (await self._collection.find_one({"_id": media_group_id}))["messages"]
        
        messages = [types.Message(**json.loads(m)) for m in raw_messages]
        messages.sort(key=lambda m: m.message_id)

        return messages

    async def delete_media_group(self, media_group_id: str):
        await self._collection.delete_one({"_id": media_group_id})
