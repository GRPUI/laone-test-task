from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

MAIN_PAGE_INLINE = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Получить информацию по товару", callback_data="get_product_data"),
        ],
        [
            InlineKeyboardButton(text="Остановить уведомления", callback_data="disable_notifications"),
        ],
        [
            InlineKeyboardButton(text="Получить информацию из БД", callback_data="get_data_from_db"),
        ]
    ]
)
