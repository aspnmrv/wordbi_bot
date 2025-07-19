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


def reconnect():
    """"""
    global CONN_GLOBAL
    if CONN_GLOBAL.closed == 1:
        CONN_GLOBAL = connect_from_config(CONFIG_PATH)


async def is_exist_temp_db(table_name: str, user_id: int, field: str = "user_id") -> bool:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT {field}
        FROM {table_name}
        WHERE {field} = %s
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return bool(data)


async def is_user_exist_db(user_id: int) -> bool:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT id
        FROM public.users
        WHERE id = %s
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return bool(data)


async def update_data_users_db(data) -> None:
    id = data.id
    first_name = data.first_name
    last_name = data.last_name
    is_bot = data.bot
    premium = data.premium
    username = data.username
    lang = data.lang_code
    scam = data.scam
    access_hash = data.access_hash
    phone = data.phone
    created_at = datetime.now()

    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        INSERT INTO public.users 
            (id, created_at, first_name, last_name, is_bot, username, lang, scam, access_hash, phone, premium)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (id, created_at, first_name, last_name, is_bot, username, lang, scam, access_hash, phone, premium))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def get_user_topics_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT topics
        FROM public.user_topics
        WHERE user_id = %s
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def update_data_topics_db(user_id, topics) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id
        FROM public.user_topics
        WHERE user_id = %s
    """, (user_id,))
    df = cur.fetchall()
    created_at = datetime.now()

    if df:
        cur.execute("""
            UPDATE public.user_topics
            SET topics = %s, updated_at = %s
            WHERE user_id = %s
        """, (topics, created_at, user_id))
    else:
        cur.execute("""
            INSERT INTO public.user_topics 
                (user_id, created_at, updated_at, topics)
            VALUES (%s, %s, %s, %s)
        """, (user_id, created_at, created_at, topics))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def get_user_words_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT
            words::json->'en' as en,
            words::json->'ru' as ru
        FROM (
            SELECT
                user_id,
                words,
                row_number() over (partition by user_id order by created_at desc) as rn
            FROM public.user_words
            WHERE user_id = %s
        ) AS subq
        WHERE rn = 1
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data[0] if data else None


async def update_user_words_db(user_id, words, link) -> None:
    conn = GLOBAL_POOL.getconn()
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()

    result = {
        "en": list(words.keys()),
        "ru": [i.lower() for i in list(words.values())]
    }
    created_at = datetime.now()

    query = """
        INSERT INTO public.user_words (user_id, created_at, words, link)
        VALUES (%s, %s, %s, %s)
    """
    cur.execute(query, (user_id, created_at, json.dumps(result), link))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def get_user_level_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT level
        FROM public.user_level
        WHERE user_id = %s
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def update_user_level_db(user_id, level) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id
        FROM public.user_level
        WHERE user_id = %s
    """, (user_id,))
    df = cur.fetchall()

    created_at = datetime.now()
    if df:
        cur.execute("""
            UPDATE public.user_level
            SET level = %s, updated_at = %s
            WHERE user_id = %s
        """, (level, created_at, user_id))
    else:
        cur.execute("""
            INSERT INTO public.user_level (user_id, created_at, updated_at, level)
            VALUES (%s, %s, %s, %s)
        """, (user_id, created_at, created_at, level))

    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def update_messages_db(user_id, mode, from_, to_, text) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    query = """
        INSERT INTO public.ellie_messages (created_at, user_id, mode, from_, to_, text)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (created_at, user_id, mode, from_, to_, text))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def update_reviews_db(user_id, text) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    query = """
        INSERT INTO public.reviews (user_id, created_at, text)
        VALUES (%s, %s, %s)
    """
    cur.execute(query, (user_id, created_at, text))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def update_data_events_db(user_id, event, params) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    query = """
        INSERT INTO public.events (user_id, created_at, event_type, params)
        VALUES (%s, %s, %s, %s)
    """
    cur.execute(query, (user_id, created_at, event, json.dumps(params)))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def get_event_from_db(user_id, event):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()

    query = """
        SELECT max(created_at) as created_at
        FROM events
        WHERE user_id = %s AND event_type = %s
    """
    cur.execute(query, (user_id, event))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0][0] if data else None


async def get_stat_use_message_db(user_id) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")

    query = """
        SELECT count(*) as cnt
        FROM public.events
        WHERE user_id = %s
            AND created_at::date = %s
            AND event_type IN ('message_from_user_quiz', 'message_from_user_conv')
    """
    cur.execute(query, (user_id, date))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def get_stat_use_mode_db(user_id) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")

    query = """
        SELECT count(*) as cnt
        FROM public.events
        WHERE user_id = %s
            AND created_at::date = %s
            AND event_type IN ('talking', 'quiz_me')
    """
    cur.execute(query, (user_id, date))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def get_stat_use_link_db(user_id) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")

    query = """
        SELECT count(*) as cnt
        FROM public.events
        WHERE user_id = %s
            AND created_at::date = %s
            AND event_type = 'cards_from_link_success'
    """
    cur.execute(query, (user_id, date))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def update_error_logs_db(user_id, error) -> None:
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()

    query = """
        INSERT INTO public.error_logs (user_id, created_at, error)
        VALUES (%s, %s, %s)
    """
    cur.execute(query, (user_id, created_at, error))
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def get_history_chat_ellie_db(user_id, mode):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        WITH messages_view AS (
            SELECT
                from_,
                to_,
                text,
                row_number() over (partition by user_id order by created_at desc) as rn,
                created_at
            FROM public.ellie_messages
            WHERE user_id = %s
              AND mode = %s
        )
        SELECT
            from_,
            to_,
            text
        FROM messages_view
        WHERE rn <= 10
        ORDER BY created_at
    """
    cur.execute(query, (user_id, mode))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return data if data else None


async def get_last_message_ellie_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        WITH messages_view AS (
            SELECT
                from_,
                to_,
                text,
                row_number() over (partition by user_id order by created_at desc) as rn,
                created_at
            FROM public.ellie_messages
            WHERE user_id = %s
              AND from_ = 'ellie'
        )
        SELECT
            text
        FROM messages_view
        WHERE rn = 1
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return data[0] if data else None


async def get_user_for_notify_db():
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        WITH users_with_starting_cte AS (
            SELECT DISTINCT user_id
            FROM public.users
            WHERE event_type IN ('start', 'begin')
        ),
        users_without_message_cte AS (
            SELECT DISTINCT user_id
            FROM public.users
            WHERE event_type NOT IN ('cards', 'cards_interests', 'quiz_me', 'talking')
        )
        SELECT array_agg(users_with_starting_cte.user_id)
        FROM users_with_starting_cte
        INNER JOIN users_without_message_cte
            ON users_without_message_cte.user_id = users_with_starting_cte.user_id
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def get_user_for_notify_reviews_db():
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        WITH users_with_starting_cte AS (
            SELECT DISTINCT user_id
            FROM public.events
            WHERE event_type IN ('cards', 'cards_interests', 'quiz_me', 'talking')
        ),
        users_without_review_cte AS (
            SELECT DISTINCT user_id
            FROM public.events
            WHERE event_type NOT IN ('reviews', 'leave_feedback')
        )
        SELECT array_agg(users_with_starting_cte.user_id)
        FROM users_with_starting_cte
        INNER JOIN users_without_review_cte
            ON users_without_review_cte.user_id = users_with_starting_cte.user_id
        WHERE users_with_starting_cte.user_id != %s
    """
    cur.execute(query, (5822393006,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def get_private_db():
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT
            count(DISTINCT CASE WHEN event_type = 'start' THEN user_id ELSE NULL END) AS users_starting,
            count(DISTINCT CASE WHEN event_type IN ('quiz_me', 'talking') THEN user_id ELSE NULL END) AS users_ellie,
            count(DISTINCT CASE WHEN event_type IN ('cards', 'cards_interests') THEN user_id ELSE NULL END) AS users_cards,
            count(DISTINCT CASE WHEN event_type = 'success_review' THEN user_id ELSE NULL END) AS users_reviews
        FROM events
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data[0] if data else None


async def get_num_translates_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        WITH stat_view AS (
            SELECT COUNT(*) AS cnt
            FROM public.events
            WHERE user_id = %s
              AND event_type = 'translate_message_success'
        )
        SELECT cnt FROM stat_view
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return data[0][0] if data else None


async def update_user_stat_words_db(user_id, word) -> None:
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        INSERT INTO public.user_stat_new_words (user_id, word, created_at)
        VALUES (%s, %s, %s)
    """
    cur.execute(query, (user_id, word, created_at))
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def update_user_stat_learned_words_db(user_id, word) -> None:
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        INSERT INTO public.user_stat_learned_words (user_id, word, created_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, word)
        DO UPDATE SET created_at = EXCLUDED.created_at
    """
    cur.execute(query, (user_id, word, created_at))
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def update_user_stat_category_words_db(user_id, words, category, is_system) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    for word, translate in words.items():
        query = """
            INSERT INTO public.user_stat_words_category
                (user_id, created_at, category, word, translate, updated_at, is_system)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, category, word) DO NOTHING
        """
        cur.execute(query, (user_id, created_at, category, word, translate, created_at, is_system))

    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def update_user_stat_category_words_batches_db(user_id, words, category, is_system) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    values = [
        (user_id, created_at, category, word, translate, created_at, is_system)
        for word, translate in words.items()
    ]

    query = """
        INSERT INTO public.user_stat_words_category 
        (user_id, created_at, category, word, translate, updated_at, is_system)
        VALUES %s
        ON CONFLICT (user_id, category, word) DO NOTHING
    """

    execute_values(cur, query, values)

    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def update_user_self_category_words_db(user_id, category, is_system=False) -> None:
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    query = """
        UPDATE public.user_stat_words_category
        SET category = %s, updated_at = %s, is_system = %s
        WHERE user_id = %s AND category = 'tmp349201'
    """
    cur.execute(query, (category, created_at, is_system, user_id))

    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def delete_category_for_user(user_id, category, is_system=False):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM public.user_stat_words_category
        WHERE user_id = %s AND category = %s AND is_system = %s
    """, (user_id, category, is_system))
    conn.commit()
    GLOBAL_POOL.putconn(conn)


async def get_user_categories_db(user_id, is_system=False):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT DISTINCT category
        FROM public.user_stat_words_category
        WHERE user_id = %s AND is_system = %s
    """
    cur.execute(query, (user_id, is_system))
    result = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return [r[0] for r in result if r[0] not in ("tmp349201", None, "")]


async def get_user_words_by_category_db(user_id, category, is_system=False):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT word, translate
        FROM public.user_stat_words_category
        WHERE user_id = %s AND category = %s AND is_system = %s
    """
    cur.execute(query, (user_id, category, is_system))
    words = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return {w[0]: w[1] for w in words} if words else None


async def get_user_one_word_db(user_id, category, word, is_system=False):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT word, translate
        FROM public.user_stat_words_category
        WHERE user_id = %s AND category = %s AND is_system = %s AND word = %s
        LIMIT 1
    """
    cur.execute(query, (user_id, category, is_system, word))
    words = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return (words[0][0], words[0][1]) if words else None


async def get_user_stat_new_words_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT
            date_trunc('day', created_at)::date AS dt,
            count(*) AS words
        FROM public.user_stat_new_words
        WHERE user_id = %s
        GROUP BY dt
        ORDER BY dt
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data if data else []


async def get_user_stat_learned_words_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        SELECT
            date_trunc('day', created_at)::date AS dt,
            count(*) AS words
        FROM public.user_stat_learned_words
        WHERE user_id = %s
        GROUP BY dt
        ORDER BY dt
    """
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data if data else []


async def get_user_stat_total_db(user_id):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = """
        WITH new_words_cte AS (
            SELECT
                n.user_id,
                n.word,
                c.category
            FROM public.user_stat_new_words n
            LEFT JOIN public.user_stat_words_category c
                ON n.user_id = c.user_id AND lower(n.word) = lower(c.word)
            WHERE n.user_id = %s
        ),

        learned_words_cte AS (
            SELECT
                l.user_id,
                l.word,
                c.category
            FROM public.user_stat_learned_words l
            LEFT JOIN public.user_stat_words_category c
                ON l.user_id = c.user_id AND lower(l.word) = lower(c.word)
            WHERE l.user_id = %s
        ),

        result_cte AS (
            SELECT
                n.category,
                count(n.word) AS words,
                count(CASE WHEN l.word IS NOT NULL THEN n.word ELSE NULL END) AS learned_words
            FROM new_words_cte n
            LEFT JOIN learned_words_cte l
                ON l.user_id = n.user_id AND lower(l.word) = lower(n.word)
            GROUP BY n.category
        )

        SELECT
            category,
            words,
            learned_words,
            CASE WHEN words > 0 THEN learned_words::float / words::float * 100 ELSE 0 END AS share_learned_words
        FROM result_cte
        ORDER BY learned_words DESC
        LIMIT 7
    """
    cur.execute(query, (user_id, user_id))
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data if data else []


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
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.sender_id if hasattr(event, 'sender_id') else event.message.peer_id.user_id
            if not await increment_counter_and_check(user_id, counter_type, limit):
                await event.client.send_message(
                    event.chat_id,
                    "Ого, какая активность! Но я не успеваю справляться с такой нагрузкой 😔\n\n"
                    "Попробуй воспользоваться этой функцией завтра 💜"
                )
                return
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator


async def mark_word_as_hard_db(user_id, word, category, is_system):
    conn = GLOBAL_POOL.getconn()
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO user_hard_words (user_id, word, category, is_system)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, word, category, is_system)
                DO UPDATE SET last_failed_at = NOW(), is_learned = FALSE;
            """
            cur.execute(query, (user_id, word, category, is_system))
        conn.commit()
    finally:
        GLOBAL_POOL.putconn(conn)


def mark_word_as_learned_db(user_id, word, category, is_system):
    conn = GLOBAL_POOL.getconn()
    try:
        with conn.cursor() as cur:
            query = """
                UPDATE user_hard_words
                SET is_learned = TRUE
                WHERE user_id = %s AND word = %s AND category = %s AND is_system = %s;
            """
            cur.execute(query, (user_id, word, category, is_system))
        conn.commit()
    finally:
        GLOBAL_POOL.putconn(conn)


def get_user_hard_words_for_testing(user_id):
    conn = GLOBAL_POOL.getconn()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT word FROM user_hard_words
                WHERE user_id = %s AND is_learned = FALSE
                ORDER BY last_failed_at DESC
                LIMIT 30;
            """
            cur.execute(query, (user_id,))
            rows = cur.fetchall()
            return [row[0] for row in rows]  # row[0] = word
    finally:
        GLOBAL_POOL.putconn(conn)
