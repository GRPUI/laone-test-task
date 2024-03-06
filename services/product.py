import aiohttp
from typing import Dict


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
