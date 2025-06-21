# Wordbi bot (to learn English words)

Wordbi is a telegram bot to help you learn English words through word cards and communication with AI.

## Description

The bot allows you to create word cards based on your interests and language level, and there is also the ability to study words with the AI ​​bot in study mode or just chat.

You can start using it [here](https://t.me/wordbi_bot)

## About the code:

This project is a modular bot, made using Python 3 and the following:

- [Telethon Library (Client API & Bot API)](https://github.com/LonamiWebs/Telethon)
- LLM models (OpenAI) for talking to AI bot

## Bot features:

The goal of the bot is to provide Telegram users with a simple interface for learning words at any time. The user can choose the learning mode, as well as monitor their statistics.

At the moment the bot is adapted only for Russian language. You can contribute and add your own languages ​​if you want :)

The main features of the bot:

- Сhoice of language level
- Сhoice of user interests
- Ability to create word cards on any interesting topic (within reason, of course)
- Ability to switch to word learning mode in a dialogue with AI
- Ability to chat on any topic with AI
- Ability to take tests based on the words you've learned


## Usage

- run (/start)
- choose your interests
- select language level
- select training mode
- when selecting the "Word Cards" mode, you can create word cards based on already selected interests or create your own word cards on any topic. 
- when selecting the "Word Cards" mode, you can flip through the cards / turn over the cards and take a test based on the words you are learning
- when choosing the "Chat with Ellie" method, you can choose the "Quiz me" mode, when Ellie AI will ask you the words you have learned and correct mistakes.
- when choosing the "Chat with Ellie" method, you can also choose the "Chat" mode, when you can talk about an interesting topic with Ellie AI.
- there is also an option to view your statistics on the /my_stat command

## Setting up the bot

Before all, clone this repository.

You need to add a config with filled parameters for the [telegram api](https://core.telegram.org/api) and also it is necessary to have a personal [key](https://platform.openai.com/api-keys) to access the work of OpenAI models:

```
BOT_TOKEN: "your_bot_token"
APP_ID: "your_bot_app_id"
API_HASH: "your_bot_api_hash"
BOT_API: "your_bot_api"
API_KEY: "your_api_key_openai"
TEST_USER_ID: "your_telegram_user_id"
```

### Without Docker

Run main file nohup venv/bin/python -m bot.main > out.log 2>&1 &

### Database

The bot depends on sqlite database and Postgres database.

For the bot to work, you need to connect to the Postgres database by filling out the config/config.json:

```
{
  "dbname": "",
  "user": "",
  "password": "",
  "host": "",
  "port": "",
  "sslmode": ""
}
```

Postgres Database structure:

Tables:

- ellie_messages
  ```
CREATE TABLE ellie_messages (
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    user_id BIGINT NOT NULL,
    mode VARCHAR,
    from_ VARCHAR,
    to_ VARCHAR,
    text TEXT
);

  ```

- error_logs
  ```
CREATE TABLE error_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    error TEXT
);

  ```

- events
  ```
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    event_type VARCHAR,
    params JSON
);

  ```

- reviews
  ```
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    text TEXT
);

  ```

- user_level
  ```
CREATE TABLE user_level (
    user_id BIGINT NOT NULL PRIMARY KEY,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    level VARCHAR
);

  ```

- user_self_words
  ```
CREATE TABLE user_self_words (
    user_id BIGINT NOT NULL PRIMARY KEY,
    words TEXT
);

  ```

- user_stat_learned_words
  ```
CREATE TABLE user_stat_learned_words (
    user_id BIGINT,
    word VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE
);

  ```

- user_stat_new_words
  ```
CREATE TABLE user_stat_new_words (
    user_id BIGINT,
    word VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE
);

  ```

- user_stat_words_category
  ```
CREATE TABLE user_stat_words_category (
    user_id BIGINT,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    category VARCHAR,
    word VARCHAR,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

  ```

- user_topics
  ```
CREATE TABLE user_topics (
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    topics VARCHAR[]
);

  ```

- user_words
  ```
CREATE TABLE user_words (
    user_id BIGINT,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    words VARCHAR,
    link VARCHAR
);

  ```

- users
  ```
CREATE TABLE users (
    id BIGINT NOT NULL PRIMARY KEY,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    is_bot BOOLEAN,
    username VARCHAR,
    lang VARCHAR,
    scam BOOLEAN,
    access_hash VARCHAR,
    phone VARCHAR,
    premium BOOLEAN
);

  ```

## Authors

Contributors names and contact info

ex. Artem Ponomarev
ex. [@aspnmrv](https://t.me/aspnmrv)
