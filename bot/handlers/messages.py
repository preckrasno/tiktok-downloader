# bot/handlers/messages.py

from aiogram.types import Message
from bot import bot, dp
from bot.api.tiktok import TikTokAPI

TikTok = TikTokAPI(
    headers={
        "Referer": "https://www.tiktok.com/",
    }
)

@dp.message_handler(content_types=["text"])
@dp.channel_post_handler(content_types=["text"])
async def get_message(message: Message):
    async for video in TikTok.handle_message(message):
        if not video:
            continue
        await bot.send_video(
            message.chat.id,
            video,
            reply_to_message_id=message.message_id,
        )
