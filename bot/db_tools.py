import ast
import sqlite3
import json
import os

from pathlib import Path

# DB_PATH = Path(__file__).parent.parent.resolve() / "data"
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
        CREATE TABLE IF NOT EXISTS user_test_words
              (user_id INT, word TEXT)
        """
    )
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
    else:
        query = f"""
            SELECT
                states
            FROM user_states_temp
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
    else:
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
    if data:
        data = ast.literal_eval(data[0][0])

    return data if data else None


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
