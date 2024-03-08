import asyncio
import os

import dotenv
import requests
from celery import Celery
from sqlalchemy.orm import Session

from services.product import get_product_data
from models.subscription import Subscription

from sqlalchemy import create_engine


app = Celery(
    'tasks',
    broker='amqp://rmuser:rmpassword@rabbitmq:5672',
    timezone='Asia/Novosibirsk',
    enable_utc=False,
)
app.conf.broker_connection_retry_on_startup = True
app.conf.beat_schedule = {
    'send-notification': {
        'task': 'services.tasks.send_notification',
        'schedule': 300,
    },
}

dotenv.load_dotenv()
database = os.getenv(key="DB_NAME")
user = os.getenv(key="POSTGRES_USER")
password = os.getenv(key="DB_PASSWORD")
host = os.getenv(key="DB_HOST")
port = os.getenv(key="DB_PORT")
engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}')

@app.task()
def send_notification():
    with engine.connect() as connection:
        with Session(connection) as session:
            results = session.query(Subscription).all()
            for result in results:
                product_info = asyncio.run(get_product_data(result.product_id))
                token = os.getenv("API_TOKEN")
                text = (f'Специальное предложение! '
                        f'Закажите \"{product_info["name"]}\" с артикулом {product_info["id"]}. Этот '
                        f'товар с рейтингом {product_info["rating"]} доступен в ограниченном количестве - '
                        f'всего {product_info["quantity"]} штуки. '
                        f'Сейчас вы можете купить его со скидкой и заплатить всего {product_info["price_with_discount"]} '
                        f'рублей вместо {product_info["price"]} рублей. Не упустите свою выгоду!')
                requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={result.user_id}&text={text}")


if __name__ == '__main__':
    send_notification()