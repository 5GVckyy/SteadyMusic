import asyncio
from os import path
import psutil

from pyrogram import Client
from pyrogram import filters
from pyrogram.types import (InlineKeyboardMarkup, InputMediaPhoto, Message,
                            Voice, InlineKeyboardButton)
from youtube_search import YoutubeSearch

from Yukki import (BOT_USERNAME, DURATION_LIMIT, DURATION_LIMIT_MIN,
                   MUSIC_BOT_NAME, app, db_mem)
from Yukki.Core.PyTgCalls.Converter import convert
from Yukki.Core.PyTgCalls.Downloader import download
from Yukki.Decorators.assistant import AssistantAdd
from Yukki.Decorators.checker import checker
from Yukki.Decorators.permission import PermissionCheck
from Yukki.Inline import (playlist_markup, search_markup, search_markup2,
                          url_markup, url_markup2)
from Yukki.Utilities.changers import seconds_to_min, time_to_seconds
from Yukki.Utilities.chat import specialfont_to_normal
from Yukki.Utilities.stream import start_stream, start_stream_audio
from Yukki.Utilities.theme import check_theme
from Yukki.Utilities.thumbnails import gen_thumb
from Yukki.Utilities.url import get_url
from Yukki.Utilities.youtube import (get_yt_info_id, get_yt_info_query,
                                     get_yt_info_query_slider)

from Yukki.Core.Clients.cli import app, userbot, call_py
from Yukki.Driver.queues import QUEUE, add_to_queue, clear_queue
# from Yukki.Driver.amay import call_py, user, bot
from config import IMG_1, IMG_2, SUPPORT_CHANNEL, SUPPORT_GROUP
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo,
)
from youtubesearchpython import VideosSearch
DISABLED_GROUPS = []

loop = asyncio.get_event_loop()

@app.on_message(
    filters.command(["play", f"play@{BOT_USERNAME}"]) & filters.group
)
@checker
@PermissionCheck
@AssistantAdd
async def play(_, message: Message):
    if message.chat.id in DISABLED_GROUPS:
        return
    await message.delete()
    if message.chat.id not in db_mem:
        db_mem[message.chat.id] = {}
    if message.sender_chat:
        return await message.reply_text(
            "You're an __Anonymous Admin__ in this Chat Group!\nRevert back to User Account From Admin Rights."
        )
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    url = get_url(message)
    if audio:
        mystic = await message.reply_text(
            "🔄 Processing Audio... Please Wait!"
        )

        if audio.file_size > 157286400:
            return await mystic.edit_text(
                "Audio File Size Should Be Less Than 150 mb"
            )
        duration_min = seconds_to_min(audio.duration)
        duration_sec = audio.duration
        if (audio.duration) > DURATION_LIMIT:
            return await mystic.edit_text(
                f"**Duration Limit Exceeded**\n\n**Allowed Duration: **{DURATION_LIMIT_MIN} minute(s)\n**Received Duration:** {duration_min} minute(s)"
            )
        file_name = (
            audio.file_unique_id
            + "."
            + (
                (audio.file_name.split(".")[-1])
                if (not isinstance(audio, Voice))
                else "ogg"
            )
        )
        file_name = path.join(path.realpath("downloads"), file_name)
        file = await convert(
            (await message.reply_to_message.download(file_name))
            if (not path.isfile(file_name))
            else file_name,
        )
        return await start_stream_audio(
            message,
            file,
            "smex1",
            "Given Audio Via Telegram",
            duration_min,
            duration_sec,
            mystic,
        )
    elif url:
        mystic = await message.reply_text("🔄 Processing URL... Please Wait!")
        query = message.text.split(None, 1)[1]
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query(query)
        await mystic.delete()
        buttons = url_markup2(videoid, duration_min, message.from_user.id)
        return await message.reply_photo(
            photo=thumb,
            caption=f"📎Title: **{title}\n\n⏳Duration:** {duration_min} Mins\n\n__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{videoid})__",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        if len(message.command) < 2:
            buttons = playlist_markup(
                message.from_user.first_name, message.from_user.id, "abcd"
            )
            await message.reply_photo(
                photo="Utils/Playlist.jpg",
                caption=(
                    "**Usage:** /play [Music Name or Youtube Link or Reply to Audio]\n\nIf you want to play Playlists! Select the one from Below."
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return
        mystic = await message.reply_text("🔍 **Searching**...")
        query = message.text.split(None, 1)[1]
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query(query)
        await mystic.delete()
        buttons = url_markup(
            videoid, duration_min, message.from_user.id, query, 0
        )
        return await message.reply_photo(
            photo=thumb,
            caption=f"📎Title: **{title}\n\n⏳Duration:** {duration_min} Mins\n\n__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{videoid})__",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@app.on_callback_query(filters.regex(pattern=r"Yukki"))
async def startyuplay(_, CallbackQuery):
    if CallbackQuery.message.chat.id not in db_mem:
        db_mem[CallbackQuery.message.chat.id] = {}
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    chat_id = CallbackQuery.message.chat.id
    chat_title = CallbackQuery.message.chat.title
    videoid, duration, user_id = callback_request.split("|")
    if str(duration) == "None":
        return await CallbackQuery.answer(
            f"Sorry! Its a Live Video.", show_alert=True
        )
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "This is not for you! Search You Own Song.", show_alert=True
        )
    await CallbackQuery.message.delete()
    title, duration_min, duration_sec, thumbnail = get_yt_info_id(videoid)
    if duration_sec > DURATION_LIMIT:
        return await CallbackQuery.message.reply_text(
            f"**Duration Limit Exceeded**\n\n**Allowed Duration: **{DURATION_LIMIT_MIN} minute(s)\n**Received Duration:** {duration_min} minute(s)"
        )
    await CallbackQuery.answer(f"Processing:- {title[:20]}", show_alert=True)
    mystic = await CallbackQuery.message.reply_text(
        f"**{MUSIC_BOT_NAME} Downloader**\n\n**Title:** {title[:50]}\n\n0% ▓▓▓▓▓▓▓▓▓▓▓▓ 100%"
    )
    downloaded_file = await loop.run_in_executor(
        None, download, videoid, mystic, title
    )
    raw_path = await convert(downloaded_file)
    theme = await check_theme(chat_id)
    chat_title = await specialfont_to_normal(chat_title)
    thumb = await gen_thumb(thumbnail, title, user_id, theme, chat_title)
    if chat_id not in db_mem:
        db_mem[chat_id] = {}
    await start_stream(
        CallbackQuery,
        raw_path,
        videoid,
        thumb,
        title,
        duration_min,
        duration_sec,
        mystic,
    )


@app.on_callback_query(filters.regex(pattern=r"Search"))
async def search_query_more(_, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "Search Your Own Music. You're not allowed to use this button.",
            show_alert=True,
        )
    await CallbackQuery.answer("Searching More Results")
    results = YoutubeSearch(query, max_results=5).to_dict()
    med = InputMediaPhoto(
        media="Utils/Result.JPEG",
        caption=(
            f"1️⃣<b>{results[0]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[0]['id']})__</u>\n\n2️⃣<b>{results[1]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[1]['id']})__</u>\n\n3️⃣<b>{results[2]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[2]['id']})__</u>\n\n4️⃣<b>{results[3]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[3]['id']})__</u>\n\n5️⃣<b>{results[4]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[4]['id']})__</u>"
        ),
    )
    buttons = search_markup(
        results[0]["id"],
        results[1]["id"],
        results[2]["id"],
        results[3]["id"],
        results[4]["id"],
        results[0]["duration"],
        results[1]["duration"],
        results[2]["duration"],
        results[3]["duration"],
        results[4]["duration"],
        user_id,
        query,
    )
    return await CallbackQuery.edit_message_media(
        media=med, reply_markup=InlineKeyboardMarkup(buttons)
    )


@app.on_callback_query(filters.regex(pattern=r"popat"))
async def popat(_, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    userid = CallbackQuery.from_user.id
    i, query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "This is not for you! Search You Own Song", show_alert=True
        )
    results = YoutubeSearch(query, max_results=10).to_dict()
    if int(i) == 1:
        buttons = search_markup2(
            results[5]["id"],
            results[6]["id"],
            results[7]["id"],
            results[8]["id"],
            results[9]["id"],
            results[5]["duration"],
            results[6]["duration"],
            results[7]["duration"],
            results[8]["duration"],
            results[9]["duration"],
            user_id,
            query,
        )
        await CallbackQuery.edit_message_text(
            f"6️⃣<b>{results[5]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[5]['id']})__</u>\n\n7️⃣<b>{results[6]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[6]['id']})__</u>\n\n8️⃣<b>{results[7]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[7]['id']})__</u>\n\n9️⃣<b>{results[8]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[8]['id']})__</u>\n\n🔟<b>{results[9]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[9]['id']})__</u>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        disable_web_page_preview = True
        return
    if int(i) == 2:
        buttons = search_markup(
            results[0]["id"],
            results[1]["id"],
            results[2]["id"],
            results[3]["id"],
            results[4]["id"],
            results[0]["duration"],
            results[1]["duration"],
            results[2]["duration"],
            results[3]["duration"],
            results[4]["duration"],
            user_id,
            query,
        )
        await CallbackQuery.edit_message_text(
            f"1️⃣<b>{results[0]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[0]['id']})__</u>\n\n2️⃣<b>{results[1]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[1]['id']})__</u>\n\n3️⃣<b>{results[2]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[2]['id']})__</u>\n\n4️⃣<b>{results[3]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[3]['id']})__</u>\n\n5️⃣<b>{results[4]['title']}</b>\n  ┗  🔗 <u>__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{results[4]['id']})__</u>",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        disable_web_page_preview = True
        return


@app.on_callback_query(filters.regex(pattern=r"slider"))
async def slider_query_results(_, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    what, type, query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "Search Your Own Music. You're not allowed to use this button.",
            show_alert=True,
        )
    what = str(what)
    type = int(type)
    if what == "F":
        if type == 9:
            query_type = 0
        else:
            query_type = int(type + 1)
        await CallbackQuery.answer("Getting Next Result", show_alert=True)
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query_slider(query, query_type)
        buttons = url_markup(
            videoid, duration_min, user_id, query, query_type
        )
        med = InputMediaPhoto(
            media=thumb,
            caption=f"📎Title: **{title}\n\n⏳Duration:** {duration_min} Mins\n\n__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{videoid})__",
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
    if what == "B":
        if type == 0:
            query_type = 9
        else:
            query_type = int(type - 1)
        await CallbackQuery.answer("Getting Previous Result", show_alert=True)
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query_slider(query, query_type)
        buttons = url_markup(
            videoid, duration_min, user_id, query, query_type
        )
        med = InputMediaPhoto(
            media=thumb,
            caption=f"📎Title: **{title}\n\n⏳Duration:** {duration_min} Mins\n\n__[Powered By {MUSIC_BOT_NAME} ✨](https://t.me/{BOT_USERNAME}?start=info_{videoid})__",
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )

#playmusic

@app.on_message(filters.command("playmusic") & filters.group & ~filters.edited & ~filters.via_bot & ~filters.forwarded)
async def hfmm(c: Client, m: Message):
    global DISABLED_GROUPS
    try:
        m.from_user.id
    except:
        return
    if len(m.command) != 2:
        await m.reply_text(
            "Saya hanya mengenali `/playmusic on` dan hanya `/playmusic off`"
        )
        return
    status = m.text.split(None, 1)[1]
    m.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await m.reply("`Mohon Tunggu...`")
        if not m.chat.id in DISABLED_GROUPS:
            await lel.edit("Pemutar Musik Sudah Diaktifkan Di Obrolan Ini")
            return
        DISABLED_GROUPS.remove(m.chat.id)
        await lel.edit(
            f"Pemutar Musik Berhasil Diaktifkan Untuk Pengguna Dalam Obrolan {m.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await m.reply("`Mohon Tunggu...`")

        if m.chat.id in DISABLED_GROUPS:
            await lel.edit("Pemutar Musik Sudah dimatikan Dalam Obrolan Ini")
            return
        DISABLED_GROUPS.append(m.chat.id)
        await lel.edit(
            f"Pemutar Musik Berhasil Dinonaktifkan Untuk Pengguna Dalam Obrolan {m.chat.id}"
        )
    else:
        await m.reply_text(
            "Saya hanya mengenali `/playmusic on` dan hanya `/playmusic off`"
        )
        
def ytsearch(query):
    try:
        search = VideosSearch(query, limit=1)
        for r in search.result()["result"]:
            ytid = r["id"]
            if len(r["title"]) > 34:
                songname = r["title"][:70]
            else:
                songname = r["title"]
            url = f"https://www.youtube.com/watch?v={ytid}"
        return [songname, url]
    except Exception as e:
        print(e)
        return 0

async def ytdl(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "best[height<=?720][width<=?1280]",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()

@app.on_message(filters.command("videoplay") & filters.group & ~filters.edited & ~filters.via_bot & ~filters.forwarded)
async def videoplay(c: Client, m: Message):
     
    cpu_len = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent

    replied = m.reply_to_message
    chat_id = m.chat.id
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="▶️", callback_data=f"resumecb"),
                InlineKeyboardButton(text="⏸️", callback_data=f"pausecb"),
                InlineKeyboardButton(text="⏭️", callback_data=f"skipcb"),
                InlineKeyboardButton(text="⏹️", callback_data=f"stopcb"),
            ],
            [
                InlineKeyboardButton(text="💮 Saluran", url=f"{SUPPORT_CHANNEL}"),
                InlineKeyboardButton(text="💮 Grup", url=f"{SUPPORT_GROUP}")
            ],
            [
                InlineKeyboardButton(text="🗑 Tutup", callback_data=f"close")
            ],
        ]
    )
    if m.sender_chat:
        return await m.reply_text("Anda adalah __Admin Anonim__ !\n\n» kembali ke akun pengguna dari hak admin.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡 Untuk menggunakan saya, saya harus menjadi **Administrator** dengan **izin** berikut:\n\n» ❌ __Delete messages__\n» ❌ __Restrict users__\n» ❌ __Add users__\n» ❌ __Manage video chat__\n\nData **diperbarui** secara otomatis setelah Anda **mempromosikan saya**"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
            "Tidak ada izin yang diperlukan:" + "\n\n» ❌ __Manage video chat__"
        )
        return
    if not a.can_delete_messages:
        await m.reply_text(
            "Tidak ada izin yang diperlukan:" + "\n\n» ❌ __Delete messages__"
        )
        return
    if not a.can_invite_users:
        await m.reply_text("Tidak ada izin yang diperlukan:" + "\n\n» ❌ __Add users__")
        return
    if not a.can_restrict_members:
        await m.reply_text("Tidak ada izin yang diperlukan:" + "\n\n» ❌ __Restrict users__")
        return
    try:
        ubot = await userbot.get_me()
        b = await c.get_chat_member(chat_id, ubot.id)
        if b.status == "kicked":
            await m.reply_text(
                f"@{ASSISTANT_NAME} **diblokir di grup** {m.chat.title}\n\n» **batalkan pemblokiran robot pengguna terlebih dahulu jika Anda ingin menggunakan bot ini.**"
            )
            return
    except UserNotParticipant:
        if m.chat.username:
            try:
                await user.join_chat(m.chat.username)
            except Exception as e:
                await m.reply_text(f"❌ **Pengguna robot gagal bergabung**\n\n**Alasan**: `{e}`")
                return
        else:
            try:
                pope = await c.export_chat_invite_link(chat_id)
                pepo = await c.revoke_chat_invite_link(chat_id, pope)
                await user.join_chat(pepo.invite_link)
            except UserAlreadyParticipant:
                pass
            except Exception as e:
                return await m.reply_text(
                    f"❌ **Pengguna robot gagal bergabung**\n\n**Alasan**: `{e}`"
                )

    if replied:
        if replied.video or replied.document:
            loser = await replied.reply("📥 **Mengunduh video...**")
            dl = await replied.download()
            link = replied.link
            if len(m.command) < 2:
                Q = 720
            else:
                pq = m.text.split(None, 1)[1]
                if pq == "720" or "480" or "360":
                    Q = int(pq)
                else:
                    Q = 720
                    await loser.edit(
                        "» __hanya 720, 480, 360 yang diizinkan__ \n💡 **sekarang streaming video dalam 720p**"
                    )
            try:
                if replied.video:
                    songname = replied.video.file_name[:70]
                elif replied.document:
                    songname = replied.document.file_name[:70]
            except BaseException:
                songname = "Video"

            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    caption=f"💡 **Lacak ditambahkan ke antrian**\n\n🏷 **Nama:** [{songname}]({link})\n💭 **Chat:** `{chat_id}`\n🎧 **Permintaan Oleh:** {requester}\n🔢 **Diposisi »** `{pos}`",
                    reply_markup=keyboard,
                )
            else:
                if Q == 720:
                    amaze = HighQualityVideo()
                elif Q == 480:
                    amaze = MediumQualityVideo()
                elif Q == 360:
                    amaze = LowQualityVideo()
                await call_py.join_group_call(
                    chat_id,
                    AudioVideoPiped(
                        dl,
                        HighQualityAudio(),
                        amaze,
                    ),
                    stream_type=StreamType().local_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                await m.reply_photo(
                    photo=f"{IMG_2}",
                    caption=f"👩‍💻 **Permintaan Oleh: ** {requester}\n\n💻 **RAM •┈➤** {ram}%\n💾 **CPU  • ╰┈➤** {cpu_len}%",
                    reply_markup=keyboard,
                )
        else:
            if len(m.command) < 2:
                await m.reply(
                    "» **Tidak dapat menemukan video lagu**, berikan nama video lagu yang benar. Contoh `/videoplay` [nama lagu]"
                )
            else:
                loser = await m.reply("🔎 **Mencari...**")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                Q = 720
                amaze = HighQualityVideo()

                if search == 0:
                    await loser.edit("❌ **Tidak ada hasil yang ditemukan.**")
                else:
                    songname = search[0]
                    url = search[1]
                    amay, ytlink = await ytdl(url)
                    if amay == 0:
                        await loser.edit(f"❌ yt-dli masalah terdeteksi\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Video", Q
                            )

                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=f"{IMG_1}",
                                caption=f"💡 **Lacak ditambahkan ke antrian**\n\n🏷 **Nama:** [{songname}]({url})\n💭 **Chat:** `{chat_id}`\n🎧 **Permintaan Oleh:** {requester}\n🔢 **Diposisi »** `{pos}`",
                                reply_markup=keyboard,
                            )
                        else:
                            try:
                                await call_py.join_group_call(
                                    chat_id,
                                    AudioVideoPiped(
                                        ytlink,
                                        HighQualityAudio(),
                                        amaze,
                                    ),
                                    stream_type=StreamType().local_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                                await loser.delete()
                                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                await m.reply_photo(
                                    photo=f"{IMG_2}",
                                    caption=f"👩‍💻 **Permintaan Oleh: ** {requester}\n\n💻 **RAM •┈➤** {ram}%\n💾 **CPU  • ╰┈➤** {cpu_len}%",
                                    reply_markup=keyboard,
                                )
                            except Exception as ep:
                                await loser.delete()
                                await m.reply_text(f"🚫 Terjadi Kesalahan: `{ep}`, Node Js gada ya anjinc")

    else:
        if len(m.command) < 2:
            await m.reply(
                "» **Tidak dapat menemukan video lagu**, berikan nama video lagu yang benar. Contoh `/videoplay` [nama lagu]"
            )
        else:
            loser = await m.reply("🔎 **Mencari...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            Q = 720
            amaze = HighQualityVideo()
            if search == 0:
                await loser.edit("❌ **Tidak ada hasil yang ditemukan.**")
            else:
                songname = search[0]
                url = search[1]
                amay, ytlink = await ytdl(url)
                if amay == 0:
                    await loser.edit(f"❌ yt-dl masalah terdeteksi\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                        await loser.delete()
                        requester = (
                            f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        )
                        await m.reply_photo(
                            photo=f"{IMG_1}",
                            caption=f"💡 **Lacak ditambahkan ke antrian**\n\n🏷 **Nama:** [{songname}]({url})\n💭 **Chat:** `{chat_id}`\n🎧 **Permintaan Oleh:** {requester}\n🔢 **Diposisi »** `{pos}`",
                            reply_markup=keyboard,
                        )
                    else:
                        requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        try:
                            await call_py.join_group_call(
                                chat_id,
                                AudioVideoPiped(
                                    ytlink,
                                    HighQualityAudio(),
                                    amaze,
                                ),
                                stream_type=StreamType().local_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            await m.reply_photo(
                                photo=f"{IMG_2}",
                                caption=f"👩‍💻 **Permintaan Oleh: ** {requester}\n\n💻 **RAM •┈➤** {ram}%\n💾 **CPU  • ╰┈➤** {cpu_len}%",
                                reply_markup=keyboard,
                            )
                        except Exception as ep:
                            await loser.delete()
                            await m.reply_text(f"🚫 Terjadi Kesalahan: `{ep}`, \n Error By {requester}")
                            
@app.on_message(
    filters.command(["vend", f"vend@{BOT_USERNAME}"]) & filters.group
)
async def stop(Client, m: Message):
    chat_id = m.chat.id
    if chat_id in QUEUE:
        try:
            await call_py.leave_group_call(chat_id)
            clear_queue(chat_id)
            await m.reply("✅ **Streaming telah berakhir.**")
        except Exception as e:
            await m.reply(f"🚫 **Terjadi Kesalahan:**\n\n`{e}`")
    else:
        await m.reply("❌ **Tidak ada dalam streaming**")

# Powered By Amay X Ahmad 2021
