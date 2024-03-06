from aiogram.fsm.state import StatesGroup, State


class ProductDataGet(StatesGroup):
    GET_PRODUCT_ID = State()
