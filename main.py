from aiogram import Bot, Dispatcher, types, Router
from aiogram import filters

import asyncio

from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from loguru import logger

import dotenv
import os

from sqlalchemy.ext.declarative import declarative_base

from inline_buttons import MAIN_PAGE_INLINE, follow
from states.product import ProductDataGet
from services import product

dotenv.load_dotenv()

router = Router()


@router.message(filters.Command("start"))
async def send_welcome(message: types.Message, bot: Bot) -> None:
    logger.info(f"User:{message.from_user.id} Command: /start")
    await logger.complete()
    await bot.send_message(
        message.chat.id,
        text="Приветствую! Выберите интересующий вас раздел.",
        reply_markup=MAIN_PAGE_INLINE
    )


@router.message(filters.Command("help"))
async def send_help(message: types.Message) -> None:
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
    try:
        product_id = int(product_id)
    except ValueError:
        await message.answer("Введите корректный id товара")
        return
    await state.clear()
    product_info = await product.get_product_data(product_id)
    if product_info:
        text = (f'*Специальное предложение!* '
                f'Закажите *\"{product_info["name"]}\"* с артикулом *{product_info["id"]}*. Этот '
                f'товар *с рейтингом {product_info["rating"]}* доступен в *ограниченном количестве* - '
                f'*всего {product_info["quantity"]} штуки.* '
                f'Сейчас вы можете купить его *со скидкой* и заплатить всего {product_info["price_with_discount"]} '
                f'рублей вместо *{product_info["price"]} рублей.* *Не упустите свою выгоду!*')
        markup = await follow(product_id=product_id)
        await message.answer(
            text=text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        save_request = await product.save_request(connection, message.chat.id, product_id)

        return
    await message.answer("Товар не найден")


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
        await callback_query.message.edit_text("Введите id товара:")
    elif callback_query.data.startswith("follow"):
        product_id = int(callback_query.data.split("-")[1])
        await product.follow_product(connection, product_id, callback_query.message.chat.id)
        await callback_query.message.edit_text("Вы подписались на уведомления")
    elif callback_query.data == "disable_notifications":
        await product.unfollow_product(connection, callback_query.message.chat.id)
        await callback_query.message.edit_text("Вы отписались от уведомлений")
    elif callback_query.data == "get_data_from_db":
        result = await product.get_last_request(connection)
        await callback_query.message.edit_text(f"{result}")


async def main() -> None:
    logger.info("Starting bot")
    await logger.complete()

    database = os.getenv(key="DB_NAME")
    user = os.getenv(key="POSTGRES_USER")
    password = os.getenv(key="DB_PASSWORD")
    host = os.getenv(key="DB_HOST")
    port = os.getenv(key="DB_PORT")

    connection = create_async_engine(
        f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
        echo=True
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
