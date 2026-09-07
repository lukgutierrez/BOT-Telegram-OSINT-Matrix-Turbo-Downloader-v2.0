import asyncio
from telethon import TelegramClient
from config import API_ID, API_HASH

client = TelegramClient("user_session", API_ID, API_HASH)

async def debug():
    await client.start()
    entity = await client.get_entity(-1004340179079)
    seen = set()
    async for m in client.iter_messages(entity, limit=1000):
        reply = m.reply_to
        if reply:
            rt = reply.reply_to_msg_id
            if rt and rt not in seen:
                seen.add(rt)
                media = m.media is not None
                print(f"msg_id={m.id} reply_to={rt} media={media} text={(m.text or '')[:30]}")
                if len(seen) > 40:
                    break
    print(f"distintos reply_to: {len(seen)}")

asyncio.run(debug())
