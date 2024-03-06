from aiogram import Bot, Dispatcher, types, Router
from aiogram import filters

import asyncio

from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from loguru import logger

import dotenv
import os

from inline_buttons import MAIN_PAGE_INLINE
from states.product import ProductDataGet
from services import *

dotenv.load_dotenv()

router = Router()


@router.message(filters.Command("start"))
async def send_welcome(message: types.Message, bot: Bot, connection: AsyncEngine) -> None:
    logger.info(f"User:{message.from_user.id} Command: /start")
    await logger.complete()
    await bot.send_message(
        message.chat.id,
        text="Приветствую! Выберите интересующий вас раздел.",
        reply_markup=MAIN_PAGE_INLINE
    )


@router.message(filters.Command("help"))
async def send_help(message: types.Message):
    logger.info(f"User:{message.from_user.id} Command: /help")
    await logger.complete()
    await message.answer("Для начала работы нажмите /start\n")


@router.message(filters.StateFilter(ProductDataGet.GET_PRODUCT_ID))
async def get_product_data(
        message: types.Message,
        state: FSMContext,
        connection: AsyncEngine
) -> None:
    product_id = message.text
    await state.clear()
    await message.answer(product_id)


@router.callback_query()
async def process_callback(
        callback_query: types.CallbackQuery,
        state: FSMContext,
        connection: AsyncEngine
) -> None:
    logger.info(f"User:{callback_query.from_user.id} Query: {callback_query.data}")
    await logger.complete()
    if callback_query.data == "get_product_data":
        await state.set_state(ProductDataGet.GET_PRODUCT_ID)
        await callback_query.message.answer("Введите id товара")


async def main() -> None:
    logger.info("Starting bot")
    await logger.complete()

    database = os.getenv(key="DB_NAME")
    user = os.getenv(key="POSTGRES_USER")
    password = os.getenv(key="DB_PASSWORD")
    host = os.getenv(key="DB_HOST")
    port = os.getenv(key="DB_PORT")

    connection = create_async_engine(
        f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    )

    api_token = os.getenv("API_TOKEN")
    dp = Dispatcher()
    bot = Bot(token=api_token)

    dp.workflow_data.update(
        {
            "connection": connection
        }
    )

    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.add("logs.log", level="INFO", rotation="1 week")
    asyncio.run(main())
