from functools import wraps
from datetime import datetime

import os
import sys

sys.path.append(os.path.dirname(__file__))
sys.path.insert(1, os.path.realpath(os.path.pardir))

import psycopg2
import json

from psycopg2 import pool
from psycopg2.extras import execute_values
from globals import MINCONN, MAXCONN
from datetime import datetime
from functools import wraps
from datetime import datetime
from typing import Callable


def connect_from_config(file):
    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
    }
    with open(file, 'r') as fp:
        config = json.load(fp)
    return psycopg2.connect(**config, **keepalive_kwargs)


def create_pool_from_config(minconn, maxconn, file):
    with open(file, 'r') as fp:
        config = json.load(fp)
    return pool.SimpleConnectionPool(minconn, maxconn, **config)


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "config", "config.json")
GLOBAL_POOL = create_pool_from_config(MINCONN, MAXCONN, CONFIG_PATH)


async def increment_counter_and_check(user_id: int, counter_type: str, limit: int) -> bool:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    today = datetime.today().strftime("%Y-%m-%d")
    cur.execute("""
        INSERT INTO anti_abuse_counters (user_id, counter_type, counter_value, counter_date)
        VALUES (%s, %s, 1, %s)
        ON CONFLICT (user_id, counter_type, counter_date)
        DO UPDATE SET counter_value = anti_abuse_counters.counter_value + 1
    """, (user_id, counter_type, today))
    cur.execute("""
        SELECT counter_value FROM anti_abuse_counters
        WHERE user_id = %s AND counter_type = %s AND counter_date = %s
    """, (user_id, counter_type, today))
    value = cur.fetchone()[0]
    GLOBAL_POOL.putconn(conn)
    return value <= limit


def limit_usage(counter_type: str, limit: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.sender_id if hasattr(event, "sender_id") else event.message.peer_id.user_id
            if not await increment_counter_and_check(user_id, counter_type, limit):
                await event.client.send_message(event.chat_id,
                    "Ты сегодня уже достиг лимита использования для этой функции 🛑 Попробуй завтра.")
                return
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator
