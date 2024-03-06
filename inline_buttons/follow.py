from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def follow(product_id: int):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подписаться", callback_data=f"follow-{product_id}"),
            ]
        ]
    )
    return markup
