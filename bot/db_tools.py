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
    cur = CONN.cursor()

    if field == "topics":
        query = "SELECT topics FROM user_topics_temp WHERE user_id = ?"
    elif field == "states":
        query = "SELECT states FROM user_states_temp WHERE user_id = ?"
    elif field == "topics_msg_id":
        query = "SELECT msg FROM user_msg_temp WHERE user_id = ?"
    else:
        return []

    cur.execute(query, (user_id,))
    data = cur.fetchall()
    CONN.commit()

    if data:
        raw = data[0][0]
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    return []


async def _update_user_states(user_id, field, data):
    data = json.dumps(data)
    cur = CONN.cursor()

    if field == "topics":
        cur.execute("SELECT user_id FROM user_topics_temp WHERE user_id = ?", (user_id,))
        result = cur.fetchall()
        if result:
            cur.execute(
                "UPDATE user_topics_temp SET topics = ? WHERE user_id = ?",
                (data, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO user_topics_temp (user_id, topics) VALUES (?, ?)",
                (user_id, data)
            )

    elif field == "states":
        cur.execute("SELECT user_id FROM user_states_temp WHERE user_id = ?", (user_id,))
        result = cur.fetchall()
        if result:
            cur.execute(
                "UPDATE user_states_temp SET states = ? WHERE user_id = ?",
                (data, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO user_states_temp (user_id, states) VALUES (?, ?)",
                (user_id, data)
            )

    elif field == "topics_msg_id":
        cur.execute("SELECT user_id FROM user_msg_temp WHERE user_id = ?", (user_id,))
        result = cur.fetchall()
        if result:
            cur.execute(
                "UPDATE user_msg_temp SET msg = ? WHERE user_id = ?",
                (data, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO user_msg_temp (user_id, msg) VALUES (?, ?)",
                (user_id, data)
            )

    CONN.commit()
    return


async def _get_current_user_step(user_id):
    cur = CONN.cursor()
    query = "SELECT step FROM user_step_states WHERE user_id = ?"
    cur.execute(query, (user_id,))
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
    query = "SELECT step FROM user_step_states WHERE user_id = ?"
    cur.execute(query, (user_id,))
    data = cur.fetchall()

    if len(data) == 0:
        query = "INSERT INTO user_step_states (user_id, step) VALUES (?, ?)"
        cur.execute(query, (user_id, step))
    else:
        query = "UPDATE user_step_states SET step = ? WHERE user_id = ?"
        cur.execute(query, (step, user_id))

    CONN.commit()
    return


async def _get_user_topic_words(user_id):
    cur = CONN.cursor()
    query = "SELECT topic FROM user_topic_words WHERE user_id = ?"
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    CONN.commit()

    return data if data else []


async def _update_user_topic_words(user_id, data):
    data = json.dumps(data)
    cur = CONN.cursor()
    cur.execute("SELECT user_id FROM user_topic_words WHERE user_id = ?", (user_id,))
    result = cur.fetchall()

    if result:
        query = "UPDATE user_topic_words SET topic = ? WHERE user_id = ?"
        cur.execute(query, (data, user_id))
    else:
        query = "INSERT INTO user_topic_words (user_id, topic) VALUES (?, ?)"
        cur.execute(query, (user_id, data))

    CONN.commit()
    return


async def _get_user_words(user_id):
    cur = CONN.cursor()
    query = "SELECT topic, word, lang FROM user_words WHERE user_id = ?"
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    CONN.commit()

    return data if data else []


async def _update_user_words(user_id, topic, word, lang):
    cur = CONN.cursor()
    cur.execute("SELECT user_id FROM user_words WHERE user_id = ?", (user_id,))
    result = cur.fetchall()

    if result:
        query = """
            UPDATE user_words
            SET topic = ?, word = ?, lang = ?
            WHERE user_id = ?
        """
        cur.execute(query, (topic, word, lang, user_id))
    else:
        query = """
            INSERT INTO user_words (user_id, topic, word, lang)
            VALUES (?, ?, ?, ?)
        """
        cur.execute(query, (user_id, topic, word, lang))

    CONN.commit()
    return


async def _get_user_choose_topic(user_id):
    cur = CONN.cursor()
    query = "SELECT topic FROM user_choose_topic WHERE user_id = ?"
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    CONN.commit()

    if data:
        try:
            data = json.loads(data[0][0])
        except (json.JSONDecodeError, TypeError):
            data = None

    return data if data else None


async def _update_user_choose_topic(user_id, data):
    data = json.dumps(data)
    cur = CONN.cursor()
    cur.execute("SELECT user_id FROM user_choose_topic WHERE user_id = ?", (user_id,))
    result = cur.fetchall()

    if result:
        query = "UPDATE user_choose_topic SET topic = ? WHERE user_id = ?"
        cur.execute(query, (data, user_id))
    else:
        query = "INSERT INTO user_choose_topic (user_id, topic) VALUES (?, ?)"
        cur.execute(query, (user_id, data))

    CONN.commit()
    return


async def _get_user_self_words(user_id):
    cur = CONN.cursor()
    query = "SELECT words FROM user_self_words WHERE user_id = ?"
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    CONN.commit()

    if data:
        try:
            data = json.loads(data[0][0])
        except (json.JSONDecodeError, TypeError):
            data = None

    return data if data else None


async def _update_user_self_words(user_id, data):
    data = json.dumps(data)
    cur = CONN.cursor()

    cur.execute("SELECT user_id FROM user_self_words WHERE user_id = ?", (user_id,))
    result = cur.fetchall()

    if result:
        query = """
            UPDATE user_self_words
            SET words = ?
            WHERE user_id = ?
        """
        cur.execute(query, (data, user_id))
    else:
        query = """
            INSERT INTO user_self_words (user_id, words) 
            VALUES (?, ?)
        """
        cur.execute(query, (user_id, data))

    CONN.commit()


async def _get_user_test_words(user_id):
    cur = CONN.cursor()
    query = "SELECT word FROM user_test_words WHERE user_id = ?"
    cur.execute(query, (user_id,))
    data = cur.fetchall()
    CONN.commit()

    return data[0][0].replace('"', '') if data else None


async def _update_user_test_words(user_id, data):
    data = json.dumps(data)
    cur = CONN.cursor()
    cur.execute("SELECT user_id FROM user_test_words WHERE user_id = ?", (user_id,))
    result = cur.fetchall()

    if result:
        query = "UPDATE user_test_words SET word = ? WHERE user_id = ?"
        cur.execute(query, (data, user_id))
    else:
        query = "INSERT INTO user_test_words (user_id, word) VALUES (?, ?)"
        cur.execute(query, (user_id, data))

    CONN.commit()
    return


async def _get_user_choose_category(user_id, is_system=None):
    cur = CONN.cursor()
    query = "SELECT category, is_system FROM user_choose_category WHERE user_id = ?"
    params = [user_id]

    if is_system is not None:
        query += " AND is_system = ?"
        params.append(is_system)

    cur.execute(query, tuple(params))
    data = cur.fetchall()
    CONN.commit()

    if data:
        category_raw = data[0][0]
        try:
            category = json.loads(category_raw)
        except json.JSONDecodeError:
            category = category_raw
        is_system_flag = bool(data[0][1])
        data = (category, is_system_flag)

    return data if data else None


async def _update_user_choose_category(user_id, data, is_system):
    data = json.dumps(data)
    cur = CONN.cursor()
    cur.execute("SELECT user_id FROM user_choose_category WHERE user_id = ?", (user_id,))
    result = cur.fetchall()

    if result:
        query = "UPDATE user_choose_category SET category = ?, is_system = ? WHERE user_id = ?"
        cur.execute(query, (data, is_system, user_id))
    else:
        query = "INSERT INTO user_choose_category (user_id, category, is_system) VALUES (?, ?, ?)"
        cur.execute(query, (user_id, data, is_system))

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
