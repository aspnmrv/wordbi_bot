import os
import sys

sys.path.append(os.path.dirname(__file__))
sys.path.insert(1, os.path.realpath(os.path.pardir))

import psycopg2
import json

from psycopg2 import pool
from globals import MINCONN, MAXCONN
from datetime import datetime


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
    """Check exist value in table"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            {field}
        FROM {table_name}
        WHERE {field} = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return True
    else:
        return False


async def is_user_exist_db(user_id: int) -> bool:
    """Check exist user_id in database"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            id
        FROM public.users
        WHERE id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return True
    else:
        return False


async def update_data_users_db(data) -> None:
    """"""

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
    query = f"""
        INSERT INTO public.users (id, created_at, first_name, 
            last_name, is_bot, username, lang, scam, access_hash, phone, premium)
        VALUES ({id}, '{created_at}', '{first_name}', '{last_name}', {is_bot},  
            '{username}', '{lang}', {scam}, '{access_hash}', '{phone}', {premium})
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return


async def get_user_topics_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            topics
        FROM public.user_topics
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return data[0][0]
    else:
        return None


async def update_data_topics_db(user_id, topics) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            user_id
        FROM public.user_topics
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    df = cur.fetchall()
    if df:
        created_at = datetime.now()
        query = f"""
            UPDATE public.user_topics
            SET topics = ARRAY{topics}, updated_at = '{created_at}'
            WHERE user_id = {user_id}
        """
    else:
        created_at = datetime.now()
        query = f"""
            INSERT INTO public.user_topics (user_id, created_at, updated_at, topics)
            VALUES ({user_id}, '{created_at}', '{created_at}', ARRAY{topics})
        """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return None


async def get_user_words_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            words::json->'en' as en,
            words::json->'ru' as ru
        FROM (
            SELECT
                user_id,
                words,
                row_number() over (partition by user_id order by created_at desc) as rn
            FROM public.user_words
            WHERE user_id = {user_id}
        ) AS subq
        WHERE rn = 1
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)

    if data:
        return data[0]
    else:
        return None


async def update_user_words_db(user_id, words, link) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()
    result = {
        "en": list(words.keys()),
        "ru": [i.lower() for i in list(words.values())]
    }

    created_at = datetime.now()
    query = f"""
        INSERT INTO public.user_words (user_id, created_at, words, link)
        VALUES ({user_id}, '{created_at}', '{json.dumps(result)}', '{link}')
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return None


async def get_user_level_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            level
        FROM public.user_level
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return data[0][0]
    else:
        return None


async def update_user_level_db(user_id, level) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            user_id
        FROM public.user_level
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    df = cur.fetchall()
    if df:
        created_at = datetime.now()
        query = f"""
            UPDATE public.user_level
            SET level = '{level}', updated_at = '{created_at}'
            WHERE user_id = {user_id}
        """
    else:
        created_at = datetime.now()
        query = f"""
            INSERT INTO public.user_level (user_id, created_at, updated_at, level)
            VALUES ({user_id}, '{created_at}', '{created_at}', '{level}')
        """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return None


async def update_messages_db(user_id, mode, from_, to_, text) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()
    query = f"""
        INSERT INTO public.ellie_messages (created_at, user_id, mode, from_, to_, text)
        VALUES ('{created_at}', {user_id}, '{mode}', '{from_}', '{to_}', '{text}')
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return None


async def update_reviews_db(user_id, text) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()
    query = f"""
        INSERT INTO public.reviews (user_id, created_at, text)
        VALUES ({user_id}, '{created_at}', '{text}')
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return None


async def update_data_events_db(user_id, event, params) -> None:
    """"""
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        INSERT INTO public.events (user_id, created_at, event_type, params)
        VALUES ({user_id}, '{created_at}', '{event}', '{json.dumps(params)}')
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def get_event_from_db(user_id, event):
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        SELECT
            max(created_at) as created_at
        FROM events
        WHERE user_id = {user_id}
            AND event_type = '{event}'
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0][0] if data else None


async def get_stat_use_message_db(user_id) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")
    query = f"""
        SELECT
            count(*) as cnt
        FROM public.events
        WHERE user_id = {user_id}
            and created_at::date = '{date}'
            and event_type in ('message_from_user_quiz', 'message_from_user_conv')
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0][0] if data else None


async def get_stat_use_mode_db(user_id) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")
    query = f"""
        SELECT
            count(*) as cnt
        FROM public.events
        WHERE user_id = {user_id}
            and created_at::date = '{date}'
            and event_type in ('talking', 'quiz_me')
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0][0] if data else None


async def get_stat_use_link_db(user_id) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")
    query = f"""
        SELECT
            count(*) as cnt
        FROM public.events
        WHERE user_id = {user_id}
            and created_at::date = '{date}'
            and event_type = 'cards_from_link_success'
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0][0] if data else None


async def update_error_logs_db(user_id, error) -> None:
    """"""
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        INSERT INTO public.error_logs (user_id, created_at, error)
        VALUES ({user_id}, '{created_at}', '{error}')
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def get_history_chat_ellie_db(user_id, mode):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        WITH messages_view AS (
            SELECT
                from_,
                to_,
                text,
                row_number() over (partition by user_id order by created_at desc) as rn,
                created_at
            FROM public.ellie_messages
            WHERE user_id = {user_id}
                AND mode = '{mode}'
        )
        
        SELECT
            from_,
            to_,
            text
        FROM messages_view
        WHERE rn <= 10
        order by created_at
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data if data else None


async def get_last_message_ellie_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        WITH messages_view AS (
            SELECT
                from_,
                to_,
                text,
                row_number() over (partition by user_id order by created_at desc) as rn,
                created_at
            FROM public.ellie_messages
            WHERE user_id = {user_id}
                and from_ = 'ellie'
        )

        SELECT
            text
        FROM messages_view
        WHERE rn = 1
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0] if data else None


async def get_user_for_notify_db():
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        with users_with_starting_cte as (
            SELECT distinct
                user_id
            FROM public.users
            WHERE event_type in ('start', 'begin')
        ),
        
        users_without_message_cte as (
            select distinct
                user_id
            from public.users
            where event_type not in ('cards', 'cards_interests', 'quiz_me', 'talking')
        )
        
        select
            array_agg(users_with_starting_cte.user_id)
        from users_with_starting_cte
        inner join users_without_message_cte on users_without_message_cte.user_id = users_with_starting_cte.user_id
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return data[0][0]
    else:
        return None


async def get_user_for_notify_reviews_db():
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        with users_with_starting_cte as (
            SELECT distinct
                user_id
            FROM public.events
            WHERE event_type in ('cards', 'cards_interests', 'quiz_me', 'talking')
        ),

        users_without_review_cte as (
            select distinct
                user_id
            from public.events
            where event_type not in ('reviews', 'leave_feedback')
        )

        select
            array_agg(users_with_starting_cte.user_id)
        from users_with_starting_cte
        inner join users_without_review_cte on users_without_review_cte.user_id = users_with_starting_cte.user_id
        where users_with_starting_cte.user_id != 5822393006
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return data[0][0]
    else:
        return None


async def get_private_db():
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        select
            count(distinct case when event_type in ('start')
                 then user_id else null end) as users_starting,
            count(distinct case when event_type in ('quiz_me', 'talking')
                 then user_id else null end) as users_ellie,
            count(distinct case when event_type in ('cards', 'cards_interests')
                 then user_id else null end) as users_cards,
            count(distinct case when event_type in ('success_review')
                 then user_id else null end) as users_cards
        from events
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    if data:
        return data[0]
    else:
        return None


async def get_num_translates_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        WITH stat_view AS (
            SELECT
                count(*) as cnt
            FROM public.events
            WHERE user_id = {user_id}
                and event_type = 'translate_message_success'
        )

        SELECT
            cnt
        FROM stat_view
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return data[0][0] if data else None


async def update_user_stat_words_db(user_id, word) -> None:
    """"""
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        INSERT INTO public.user_stat_new_words (user_id, word, created_at)
        VALUES ({user_id}, '{word}', '{created_at}')
        ON CONFLICT (user_id, word) DO NOTHING;
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def update_user_stat_learned_words_db(user_id, word) -> None:
    """"""
    created_at = datetime.now()
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        INSERT INTO public.user_stat_learned_words (user_id, word, created_at)
        VALUES ({user_id}, '{word}', '{created_at}')
        ON CONFLICT (user_id, word) DO NOTHING;
    """
    cur.execute(query)
    conn.commit()
    GLOBAL_POOL.putconn(conn)
    return None


async def update_user_stat_category_words_db(user_id, words, category) -> None:
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    created_at = datetime.now()

    for word in words:
        query = f"""
                INSERT INTO public.user_stat_words_category (user_id, created_at, category, word, updated_at)
                VALUES ({user_id}, '{created_at}', '{category}', '{word}', '{created_at}')
                ON CONFLICT (user_id, word)
                DO UPDATE SET category = EXCLUDED.category, updated_at = EXCLUDED.updated_at;
            """
        cur.execute(query)

    conn.commit()
    GLOBAL_POOL.putconn(conn)

    return None


async def get_user_stat_new_words_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        select
            date_trunc('day', created_at)::date as dt,
            count(*) as words
        from public.user_stat_new_words
        where user_id = {user_id}
        group by dt
        order by dt
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data if data else []


async def get_user_stat_learned_words_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        select
            date_trunc('day', created_at)::date as dt,
            count(*) as words
        from public.user_stat_learned_words
        where user_id = {user_id}
        group by dt
        order by dt
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data if data else []


async def get_user_stat_total_db(user_id):
    """"""
    conn = GLOBAL_POOL.getconn()
    cur = conn.cursor()
    query = f"""
        with new_words_cte as (
            select
                user_stat_new_words.user_id,
                user_stat_new_words.word,
                user_stat_words_category.category
            from public.user_stat_new_words
            left join public.user_stat_words_category
                on user_stat_new_words.user_id = user_stat_words_category.user_id
                and lower(user_stat_new_words.word) = lower(user_stat_words_category.word)
            where user_stat_new_words.user_id = {user_id}
        ),
        
        learned_words_cte as (
            select
                user_stat_learned_words.user_id,
                user_stat_learned_words.word,
                user_stat_words_category.category
            from public.user_stat_learned_words
            left join public.user_stat_words_category
                on user_stat_learned_words.user_id = user_stat_words_category.user_id
                and lower(user_stat_learned_words.word) = lower(user_stat_words_category.word)
            where user_stat_learned_words.user_id = {user_id}
        ),
        
        result_cte as (
            select
                new_words_cte.category,
                count(new_words_cte.word) as words,
                count(case when learned_words_cte.word is not null then 
                        new_words_cte.word else null end) as learned_words
            from new_words_cte
            left join learned_words_cte on learned_words_cte.user_id = 
                new_words_cte.user_id
                and lower(learned_words_cte.word) = lower(new_words_cte.word)
            group by new_words_cte.category
        )
        
        select
            category,
            words,
            learned_words,
            learned_words::float / words::float * 100. as share_leaned_words
        from result_cte
        order by learned_words desc
        limit 10
    """
    cur.execute(query)
    data = cur.fetchall()
    GLOBAL_POOL.putconn(conn)
    return data if data else []
