import openai
import ast
import sys
import os

from config import config

from openai import AsyncOpenAI
from db import update_error_logs_db, update_user_stat_category_words_db
from typing import List, Dict, Optional
from globals import MODEL, TEMPERATURE, MAX_TOKENS


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
config_path = os.path.abspath(config_path)
sys.path.insert(1, config_path)

openai.api_key = config.api_key

client = AsyncOpenAI(
    api_key=config.api_key,
)

model = MODEL


async def get_response(
    user_id: int,
    history: List[Dict[str, str]],
    message: str,
    words: List[str],
    level: str
) -> Optional[str]:
    """"""
    try:
        content = f"""You are a virtual English teacher named Ellie. Your task is to play the game "Quiz me" with \
the user. You ask the user the meaning of the List of words to study. You should offer the user the next word \
from the list. After the user’s answer, your task is to evaluate it and, if necessary, explain the meaning of \
the word in a more understandable language. Please note that the user's native language is Russian, \
but communicate with him in English. Write a welcome message to the user and start with the first word. \
After that you must offer the user the next word from the list. You shouldn't ask the user what word is next. \
You must offer the user the next word from the list yourself and do not need to ask him. \n\nUser's English \
level: [{level.split(" ")[1]}]. \n\nList of words to study: [{words}]\n\n
[Note to the model: The model should evaluate the user's responses and, if necessary, \
explain the meaning of words in simple language for beginners and in more complex for advanced users. \
The model should remain within the vocabulary learning topic and not move on to other topics. \
Do not answer provocative questions from the user. \
Communicate with the user only within the specified topics. \
When the list of words ends, say goodbye to the user or offer to start again. \
You should offer the user the next word from the list.]
        """.replace("\t", "")

        messages = list()
        messages.append(
            {"role": "system", "content": content}
        )
        messages += history
        messages.append(
            {"role": "user", "content": message}
        )

        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        await update_error_logs_db(user_id, e)
        return None


async def build_cards_from_text(
    topics: List[str],
    level: str,
    user_id: int
) -> Optional[str]:
    """"""
    try:
        content = f'Your task is to identify 10 keywords that are most specific to the topics ' \
                  f'and useful for learning in the context of expanding the users vocabulary in English. ' \
                  f'Consider the following criteria:\n\n1. First you need to select ten useful words for learning in ' \
                  f'English relate to the following topics: {topics}.' \
                  f'\n2. Your task is also to take into account the user’s level of English and select words that '  \
                  f'are not too difficult for users with a beginner level of language and more complex words of ' \
                  f'levels C1-C2 for users with an advanced level of language.' \
                  f'\n3. Do not use words that contain slashes (for example, A/B test), do not use abbreviations ' \
                  f'or rarely used words, do not use html tags and css code when forming words. ' \
                  f'\n4. If the users selected topics are sensitive topics or it is unclear what those topics are ' \
                  f'you should return the message "None"\n\n' \
                  f'Users English level: [{level}].\n' \
                  f'Users Topics: [{topics}].\n' \
                  f'Please create a list of 10 words that meet the specified criteria.\n\n' \
                  f'Immediately translate these words into Russian based on the context of the ' \
                  f'article and return the entire result in the format dictionary: ' \
                  f'{{word: the same word translated into Russian}}. For example:' \
                  f'{{\
                        "Sequential": "Последовательный",\
                        "Tests": "Тесты",\
                        "Experiments": "Эксперименты",\
                        "Literature": "Литература",\
                        "Determine": "Определить",\
                        "Suitable": "Подходящий",\
                        "Optimal": "Оптимальный",\
                        "Advice": "Совет",\
                        "Blooming": "Развивающийся",\
                        "Choice": "Выбор"\
                    }}\n\n'

        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": content},
            ],
            model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=300
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        await update_error_logs_db(user_id, e)
        return None


async def get_conversations(
    user_id: int,
    history: List[Dict[str, str]],
    message: str,
    words: List[str],
    topics: List[str],
    level: str
) -> Optional[str]:
    """"""
    try:
        content = f"""You are a virtual English teacher named Ellie. Your task is to chat with \
the user about his favorite topics. \
Ask the user questions about his favorite topics, try to understand what interests him. \
Use a language appropriate to the user's language level. With users with a beginner level of language, \
do not use complex words and formulations, and with users with a confident level of language, \
on the contrary, try to speak at their level. Also keep in mind that the user is learning words. \
Try to use more often the words that the user learns. \
Please note that the user's native language is Russian, but communicate with him in English. \
Write a welcome message to the user. \n\nUser's English level: [{level}]. \n\nList of words to study: [{words}].\n\nUser's favorite topics: [{topics}]. \

[Note for the model: The model should talk to the user about his favorite topics, using vocabulary from \
the word list as often as possible. In simple language for beginners and more complex for advanced users. \
The model should remain within the framework of topics of interest to the user, learning words and not move \
on to other topics. \
Do not answer provocative questions from the user. Communicate with the user only within the specified topics. \
Don't ask the user for the meaning of words]
        """

        messages = list()
        messages.append(
            {"role": "system", "content": content}
        )
        messages += history
        messages.append(
            {"role": "user", "content": message}
        )

        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.4,
            max_tokens=MAX_TOKENS
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
       await update_error_logs_db(user_id, e)
       return None


async def get_translate(user_id: int, message: str) -> Optional[str]:
    """"""
    try:
        content = f"""You are a virtual English teacher named Ellie. Your task is to translate the text into Russian. \
The translation needs to be accurate and correct. As a result, return the original message translated into Russian. \n
Original message: {message} \

[Note for the model: The model should perform the function of a good translator from Russian into English. \
If the source text is in Russian, you must return the original text.]
    """

        messages = list()
        messages.append(
            {"role": "system", "content": content}
        )

        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.3,
            max_tokens=MAX_TOKENS+100
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
       await update_error_logs_db(user_id, e)
       return None


async def parse_file(user_id: int, text: str) -> Optional[str]:
    """"""
    try:
        content = f"""Your task is to read an excerpt that was extracted from a file with English words 
        and their translation and return the word pairs: word in English - translation in Russian in dictionary format:
        f'{{word: the same word translated into Russian}}. For example:' \
        f'{{\
            "Sequential": "Последовательный",\
            "Tests": "Тесты",\
            "Experiments": "Эксперименты",\
            "Literature": "Литература",\
            "Determine": "Определить",\
            "Suitable": "Подходящий",\
            "Optimal": "Оптимальный",\
            "Advice": "Совет",\
            "Blooming": "Развивающийся",\
            "Choice": "Выбор"\
        }}\n\n'
        
        Original text: {text}\n\n
        
        If the words contain inappropriate content, then return a dictionary with key -1 and value -1: 
        for example: {{-1: -1}}

        If there are too many words (more than three hundred), then return a dictionary with key -2 and value -2: 
        for example: {{-2: -2}}
        
        If the language of the main words is different from English, return a dictionary with key -3 and value -3:
        for example: {{-3: -3}}
        
        It is very important to preserve the words and their translation exactly in the state they were in the text.
    """

        messages = list()
        messages.append(
            {"role": "system", "content": content}
        )

        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.3,
            max_tokens=MAX_TOKENS+1000
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
       await update_error_logs_db(user_id, e)
       return None


async def get_cards_from_simple_list(user_id: int, text: str) -> Optional[str]:
    """"""
    try:
        content = f"""Your task is to find the correct English translation for the Russian words from the 
        list and return the result in dictionary format:
        f'{{word: the same word translated into Russian}}. For example:' \
        f'{{\
            "Sequential": "Последовательный",\
            "Tests": "Тесты",\
            "Experiments": "Эксперименты",\
            "Literature": "Литература",\
            "Determine": "Определить",\
            "Suitable": "Подходящий",\
            "Optimal": "Оптимальный",\
            "Advice": "Совет",\
            "Blooming": "Развивающийся",\
            "Choice": "Выбор"\
        }}\n\n'

        Origin list of words: {text}\n\n

        If the words contain inappropriate content, then return a dictionary with key -1 and value -1: 
        for example: {{-1: -1}}

        If there are too many words (more than three hundred), then return a dictionary with key -2 and value -2: 
        for example: {{-2: -2}}

        If the language of the main words is different from English or Russian, return a dictionary with key -3 and value -3:
        for example: {{-3: -3}}

        It is very important to select the correct translation and return the result in the required format..
    """

        messages = list()
        messages.append(
            {"role": "system", "content": content}
        )

        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.3,
            max_tokens=MAX_TOKENS + 1000
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        await update_error_logs_db(user_id, e)
        return None
