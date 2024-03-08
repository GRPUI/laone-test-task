from datetime import datetime

import aiohttp
from typing import Dict, List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from models.request import Request
from models.subscription import Subscription


async def get_product_data(product_id: int) -> Dict[str, str]:
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as response:
            data = await response.json()
    products = data["data"]["products"]
    if not products:
        return {}
    name = products[0]["name"]
    id_ = products[0]["id"]
    price = products[0]["priceU"] / 100
    price_with_discount = products[0]["salePriceU"] / 100
    rating = products[0]["rating"]
    stocks = products[0]["sizes"][0]["stocks"]
    quantity = sum([stock["qty"] for stock in stocks])
    return {
        "name": name,
        "id": id_,
        "price": price,
        "price_with_discount": price_with_discount,
        "rating": rating,
        "quantity": quantity
    }


async def follow_product(connection: AsyncEngine, product_id: int, chat_id: int) -> None:
    async with AsyncSession(connection) as session:
        async with session.begin():
            stmt = select(Request).where(Request.user_id == chat_id, Request.product_id == product_id)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            if rows:
                return

            new_subscription = Subscription(
                user_id=chat_id,
                product_id=product_id)
            session.add(new_subscription)
            await session.commit()


async def unfollow_product(connection: AsyncEngine, chat_id: int) -> None:
    async with AsyncSession(connection) as session:
        async with session.begin():
            await session.execute(
                delete(Subscription).where(Subscription.user_id == chat_id)
            )
            await session.commit()


async def save_request(connection: AsyncEngine, user_id: int, product_id: int) -> None:
    async with AsyncSession(connection) as session:
        async with session.begin():
            new_request = Request(
                user_id=user_id,
                datetime=datetime.now(),
                product_id=product_id)
            session.add(new_request)
            await session.commit()


async def get_last_request(connection: AsyncEngine) -> List[Dict]:
    async with AsyncSession(connection) as session:
        async with session.begin():
            stmt = select(Request).order_by(Request.datetime.desc()).limit(5)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [{"user_id": row.user_id,
                     "product_id": row.product_id,
                     "datetime": row.datetime.strftime("%Y-%m-%d %H:%M:%S")} for row in rows[::-1]]