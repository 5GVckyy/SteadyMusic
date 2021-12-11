from config import API_HASH, API_ID, BOT_TOKEN, STRING
from pyrogram import Client
from pytgcalls import PyTgCalls

bot = Client(
    "YukkiMusicBot",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
)

user = Client(
    STRING,
    API_ID,
    API_HASH,
)

call_py = PyTgCalls(user)
