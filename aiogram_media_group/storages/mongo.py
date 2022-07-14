import asyncio
import datetime

from typing import List
from typing import Literal
from typing import TYPE_CHECKING

from aiogram import types

from .base import BaseStorage

if TYPE_CHECKING:
    from motor import motor_asyncio

from pymongo.errors import OperationFailure, DuplicateKeyError

try:
    import ujson as json
except ImportError:
    import json

Documents = Literal["MediaGroup", "Message"]


class MongoStorage(BaseStorage):
    def __init__(self, db: "motor_asyncio.AsyncIOMotorDatabase", prefix: str, ttl: int):
        self._ttl = ttl
        self._collection = db[prefix]
        
        loop = asyncio.get_event_loop()
        
        #  This happens when MongoDB driver is used as storage_driver argument
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._create_collection(db, prefix, ttl))
            loop.close()
        else:
            loop.create_task(self._create_collection(db, prefix, ttl))

    async def _create_collection(self, db: "motor_asyncio.AsyncIOMotorDatabase", prefix: str, ttl: int):
        try:
            if prefix not in await db.list_collection_names():
                await db.create_collection(prefix)
            
            if "expireAt" not in await self._list_index_names(db, prefix):
                await db[prefix].create_index("expireAt", expireAfterSeconds=ttl)
            
            elif ttl != self._ttl:
                self._ttl = ttl
                await db.command("collMod", prefix, index={ "keyPattern": { "expireAt": 1 }, "expireAfterSeconds": ttl })

        except OperationFailure:
            pass
    
    async def _list_index_names(self, db: "motor_asyncio.AsyncIOMotorDatabase", prefix: str) -> List[str]:
        names = []

        async for index in db[prefix].list_indexes():
            index = json.loads(json.dumps(index, default=lambda item: getattr(item, "__dict__", str(item))))
            name = list(index["key"].keys())[0]

            if name == "expireAt":
                self._ttl = index["expireAfterSeconds"]

            names.append(name)
        
        return names

    async def _create_document(self, id: str, documentType: Documents) -> bool:
        try:
            if await self._collection.find_one({"_id": id}) is None:
                if documentType == "Message":
                    await self._collection.insert_one({ "_id": id, "expireAt": datetime.datetime.utcnow() })
                elif documentType == "MediaGroup":
                    await self._collection.insert_one({ "_id": id, "messages": [] })
                return True
        except DuplicateKeyError:
            return False
        else:
            return False

    async def set_media_group_as_handled(self, media_group_id: str) -> bool:
        return await self._create_document(media_group_id, "MediaGroup")

    async def append_message_to_media_group(self, media_group_id: str, message: types.Message):
        if await self._create_document(f"{media_group_id}{message.message_id}", "Message"):
            await self._collection.update_one({ "_id": media_group_id }, { "$push": { "messages": json.dumps(message.to_python()) }})

    async def get_media_group_messages(self, media_group_id: str) -> List[types.Message]:
        raw_messages = (await self._collection.find_one({ "_id": media_group_id }))["messages"]
        
        messages = [types.Message(**json.loads(m)) for m in raw_messages]
        messages.sort(key=lambda m: m.message_id)

        return messages

    async def delete_media_group(self, media_group_id: str):
        await self._collection.delete_one({ "_id": media_group_id })
