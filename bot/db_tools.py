import ast
import sqlite3
import json
import os

from pathlib import Path

CONN = sqlite3.connect("sophie.db")


async def _create_db():
    """"""
    cur = CONN.cursor()
    cur.execute(
        """
        DROP TABLE user_test_state;
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_step_states
              (user_id INT, step INT)
        """
    )
    CONN.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_topics_temp
              (user_id INT, topics TEXT)
        """
    )
    CONN.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_states_temp
              (user_id INT, states TEXT)
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_msg_temp
              (user_id INT, msg TEXT)
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_topic_words
              (user_id INT, topic TEXT)
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_words
              (user_id INT, topic TEXT, word TEXT, lang TEXT)
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_choose_topic
              (user_id INT, topic TEXT)
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_self_words
              (user_id INT, words TEXT)
        """
    )
    CONN.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_choose_category
              (user_id INT, category TEXT, is_system BOOLEAN)
        """
    )
    CONN.commit()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_test_state
              (user_id INTEGER PRIMARY KEY, mode TEXT)
    """)
    CONN.commit()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_test_sequence (
            user_id INTEGER PRIMARY KEY,
            sequence TEXT
        )
    """)
    CONN.commit()

    return


async def _get_user_states(user_id, field):
    """"""
    cur = CONN.cursor()
    if field == "topics":
        query = f"""
            SELECT
                topics
            FROM user_topics_temp
            WHERE user_id = {user_id}
        """
    elif field == "states":
        query = f"""
            SELECT
                states
            FROM user_states_temp
            WHERE user_id = {user_id}
        """
    elif field == "topics_msg_id":
        query = f"""
                SELECT
                    msg
                FROM user_msg_temp
                WHERE user_id = {user_id}
            """

    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()
    if data:
        data = ast.literal_eval(data[0][0])

    return data if data else []


async def _update_user_states(user_id, field, data):
    """"""
    data = json.dumps(data)
    cur = CONN.cursor()
    if field == "topics":
        query = f"""
            SELECT
                user_id
            FROM user_topics_temp
            WHERE user_id = {user_id}
        """
        cur.execute(query)
        result = cur.fetchall()
        if result:
            query = f"""
                UPDATE user_topics_temp
                SET topics = '{data}'
                WHERE user_id = {user_id}
            """
        else:
            query = f"""
                INSERT INTO user_topics_temp (user_id, topics) 
                VALUES ({user_id}, '{data}') 
            """
    elif field == "states":
        query = f"""
            SELECT
                user_id
            FROM user_states_temp
            WHERE user_id = {user_id}
        """
        cur.execute(query)
        result = cur.fetchall()
        if result:
            query = f"""
                UPDATE user_states_temp
                SET states = '{data}'
                WHERE user_id = {user_id}
            """
        else:
            query = f"""
                INSERT INTO user_states_temp (user_id, states) 
                VALUES ({user_id}, '{data}') 
            """
    elif field == "topics_msg_id":
        query = f"""
                    SELECT
                        user_id
                    FROM user_msg_temp
                    WHERE user_id = {user_id}
                """
        cur.execute(query)
        result = cur.fetchall()
        if result:
            query = f"""
                UPDATE user_msg_temp
                SET msg = '{data}'
                WHERE user_id = {user_id}
            """
        else:
            query = f"""
                INSERT INTO user_msg_temp (user_id, msg) 
                VALUES ({user_id}, '{data}') 
            """
    cur.execute(query)
    CONN.commit()
    return


async def _get_current_user_step(user_id):
    cur = CONN.cursor()
    query = f"""
        SELECT
            step
        FROM user_step_states
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()

    return int(data[0][0])


async def _truncate_table():
    cur = CONN.cursor()
    query = f"""
        DELETE FROM user_step_states
    """
    cur.execute(query)
    CONN.commit()
    return


async def _update_current_user_step(user_id: int, step: int):
    cur = CONN.cursor()
    query = f"""
        SELECT
            step
        FROM user_step_states
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()

    if len(data) == 0:
        query = f"""
            INSERT INTO user_step_states
            (user_id, step) VALUES ({user_id}, {step})
        """
        cur.execute(query)
        CONN.commit()
    else:
        query = f"""
            UPDATE user_step_states
            SET step = {step}
            WHERE user_id = {user_id}
        """
        cur.execute(query)
        CONN.commit()
    return


async def _get_user_topic_words(user_id):
    """"""
    cur = CONN.cursor()
    query = f"""
        SELECT
            topic
        FROM user_topic_words
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()

    return data if data else []


async def _update_user_topic_words(user_id, data):
    """"""
    data = json.dumps(data)
    cur = CONN.cursor()
    query = f"""
        SELECT
            user_id
        FROM user_topic_words
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    result = cur.fetchall()
    if result:
        query = f"""
            UPDATE user_topic_words
            SET topic = '{data}'
            WHERE user_id = {user_id}
        """
    else:
        query = f"""
            INSERT INTO user_topic_words (user_id, topic) 
            VALUES ({user_id}, '{data}') 
        """
    cur.execute(query)
    CONN.commit()
    return


async def _get_user_words(user_id):
    """"""
    cur = CONN.cursor()
    query = f"""
        SELECT
            topic,
            word,
            lang
        FROM user_words
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()

    return data if data else []


async def _update_user_words(user_id, topic, word, lang):
    """"""
    cur = CONN.cursor()
    query = f"""
        SELECT
            user_id
        FROM user_words
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    result = cur.fetchall()
    if result:
        query = f"""
            UPDATE user_words
            SET topic = '{topic}',
            word = '{word}',
            lang = '{lang}'
            WHERE user_id = {user_id}
        """
    else:
        query = f"""
            INSERT INTO user_words (user_id, topic, word, lang) 
            VALUES ({user_id}, '{topic}', '{word}', '{lang}') 
        """
    cur.execute(query)
    CONN.commit()
    return


async def _get_user_choose_topic(user_id):
    """"""
    cur = CONN.cursor()

    query = f"""
        SELECT
            topic
        FROM user_choose_topic
        WHERE user_id = {user_id}
    """

    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()

    if data:
        data = ast.literal_eval(data[0][0])

    return data if data else None


async def _update_user_choose_topic(user_id, data):
    """"""
    data = json.dumps(data)
    cur = CONN.cursor()
    query = f"""
        SELECT
            user_id
        FROM user_choose_topic
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    result = cur.fetchall()
    if result:
        query = f"""
            UPDATE user_choose_topic
            SET topic = '{data}'
            WHERE user_id = {user_id}
        """
    else:
        query = f"""
            INSERT INTO user_choose_topic (user_id, topic) 
            VALUES ({user_id}, '{data}') 
        """

    cur.execute(query)
    CONN.commit()
    return


async def _get_user_self_words(user_id):
    """"""
    cur = CONN.cursor()

    query = f"""
        SELECT
            words
        FROM user_self_words
        WHERE user_id = {user_id}
    """

    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()
    if data:
        data = ast.literal_eval(data[0][0])

    return data if data else None


async def _update_user_self_words(user_id, data):
    """"""
    data = json.dumps(data)
    cur = CONN.cursor()
    query = f"""
        SELECT
            user_id
        FROM user_self_words
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    result = cur.fetchall()
    if result:
        query = f"""
            UPDATE user_self_words
            SET words = '{data}'
            WHERE user_id = {user_id}
        """
    else:
        query = f"""
            INSERT INTO user_self_words (user_id, words) 
            VALUES ({user_id}, '{data}') 
        """

    cur.execute(query)
    CONN.commit()
    return


async def _get_user_test_words(user_id):
    """"""
    cur = CONN.cursor()

    query = f"""
        SELECT
            word
        FROM user_test_words
        WHERE user_id = {user_id}
    """

    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()

    return data[0][0].replace('"', '') if data else None


async def _update_user_test_words(user_id, data):
    """"""
    data = json.dumps(data)
    cur = CONN.cursor()
    query = f"""
        SELECT
            user_id
        FROM user_test_words
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    result = cur.fetchall()
    if result:
        query = f"""
            UPDATE user_test_words
            SET word = '{data}'
            WHERE user_id = {user_id}
        """
    else:
        query = f"""
            INSERT INTO user_test_words (user_id, word) 
            VALUES ({user_id}, '{data}') 
        """

    cur.execute(query)
    CONN.commit()
    return


async def _get_user_choose_category(user_id, is_system=None):
    """"""
    cur = CONN.cursor()

    query = f"""
        SELECT
            category,
            is_system
        FROM user_choose_category
        WHERE user_id = {user_id}
    """
    if is_system:
        query += f"and is_system = {is_system}"

    cur.execute(query)
    data = cur.fetchall()
    CONN.commit()

    if data:
        category_raw = data[0][0]
        try:
            category = json.loads(category_raw)
        except json.JSONDecodeError:
            category = category_raw
        is_system = bool(data[0][1])
        data = (category, is_system)

    return data if data else None


async def _update_user_choose_category(user_id, data, is_system):
    """"""
    data = json.dumps(data)
    cur = CONN.cursor()
    query = f"""
        SELECT
            user_id
        FROM user_choose_category
        WHERE user_id = {user_id}
    """
    cur.execute(query)
    result = cur.fetchall()
    if result:
        query = f"""
            UPDATE user_choose_category
            SET category = '{data}', is_system = {is_system}
            WHERE user_id = {user_id}
        """
    else:
        query = f"""
            INSERT INTO user_choose_category (user_id, category, is_system) 
            VALUES ({user_id}, '{data}', {is_system}) 
        """

    cur.execute(query)
    CONN.commit()
    return


async def _update_user_main_mode(user_id, mode):
    """"""
    cur = CONN.cursor()
    query = """
        INSERT INTO user_test_state (user_id, mode)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET mode=excluded.mode
    """
    cur.execute(query, (user_id, mode))
    CONN.commit()


async def _get_user_main_mode(user_id):
    """"""
    cur = CONN.cursor()
    query = """
        SELECT mode FROM user_test_state WHERE user_id = ?
    """
    cur.execute(query, (user_id,))
    data = cur.fetchone()
    CONN.commit()
    return data[0] if data else None


async def _get_user_test_sequence(user_id):
    """"""
    cur = CONN.cursor()
    query = """
        SELECT sequence FROM user_test_sequence WHERE user_id = ?
    """
    cur.execute(query, (user_id,))
    data = cur.fetchone()
    CONN.commit()
    return json.loads(data[0]) if data else None


async def _update_user_test_sequence(user_id, sequence):
    cur = CONN.cursor()
    if sequence is None:
        query = """
            DELETE FROM user_test_sequence WHERE user_id = ?
        """
        cur.execute(query, (user_id,))
    else:
        json_sequence = json.dumps(sequence)
        query = """
            INSERT INTO user_test_sequence (user_id, sequence)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET sequence=excluded.sequence
        """
        cur.execute(query, (user_id, json_sequence))
    CONN.commit()
