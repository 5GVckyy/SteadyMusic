from config import API_HASH, API_ID, BOT_TOKEN, STRING
from pyrogram import Client
from pytgcalls import PyTgCalls

bot = Client(
    ":memory:",
    API_ID,
    API_HASH,
    BOT_TOKEN,
    plugins={"root": "Plugins"},
)

user = Client(
    STRING,
    API_ID,
    API_HASH,
)

call_py = PyTgCalls(user)
