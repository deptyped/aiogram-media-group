# aiogram-media-group

aiogram handler for media groups (also known as albums)

### Features

- aiogram 3 support
- Redis storage driver is supported and ready to work with multiple bot instances (aiogram 2 only)

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
