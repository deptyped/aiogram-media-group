# aiogram-media-group

AIOGram handler for media groups (also known as albums)

### Features

- Memory and Redis storage drivers supported
- Ready to work with multiple bot instances

### Install

```bash
pip install aiogram-media-group
# or
poetry add aiogram-media-group
```

### Usage

Minimal usage example:

```python
from aiogram_media_group import media_group_handler

@dp.message_handler(MediaGroupFilter(is_media_group=True), content_types=ContentType.PHOTO)
@media_group_handler
async def album_handler(messages: List[types.Message]):
    for message in messages:
        print(message)
```

Checkout [examples](https://github.com/deptyped/aiogram-media-group/blob/main/examples) for complete usage examples
