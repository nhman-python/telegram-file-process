import time
import os
import humanize
import re
import shelve
from pyrogram import Client, filters, enums
from pyrogram.enums import ChatAction
from pyrogram.types import Message

API_ID = 1234
API_HASH = "SDFGHJK23456"
BOT_TOKEN = "SDFGHJKGFDSDFGH:2345676543456"

# Set the maximum file size in megabytes (MB)
MAX_FILE_SIZE = 40 * 1024 * 1024  # 20 MB

# Create a Pyrogram client instance
app = Client("file-process", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Open a shelve file to store file names
file_names_shelve = shelve.open('file_names')


def validate_file_name(file_name, min_length=1, max_length=50, allowed_extensions=None):
    pattern = r'^.{' + str(min_length) + ',' + str(max_length) + r'}\.[a-zA-Z]{1,}$'
    if allowed_extensions:
        pattern = r'^.{' + str(min_length) + ',' + str(max_length) + r'}\.'
        pattern += r'(' + '|'.join(allowed_extensions) + r')$'

    # Validate the file name using the regular expression
    return bool(re.match(pattern, file_name))


async def progress(current, total, client, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5) == 0 or current == total:
        speed = current / diff
        elapsed_time = round(diff)
        eta = round((total - current) / speed)
        progress_str = f"{current * 100 / total:.1f}% בוצע ({humanize.naturalsize(current)}/{humanize.naturalsize(total)})"
        speed_str = f"{humanize.naturalsize(speed)}/שניות"
        time_str = f"{humanize.naturaldelta(elapsed_time)} חלף, {humanize.naturaldelta(eta)} נותרו"
        await message.edit(f"{progress_str}\n{speed_str}\n{time_str}")


@app.on_message(filters.command("start") & filters.private)
async def start_command(_, message: Message):
    await message.reply(
        f"👋 היי {message.from_user.mention(style=enums.ParseMode.HTML)}, אני בוט לשינוי שמות לקבצים! "
        f"רק שלח לי את השם החדש שתרצה לתת לקובץ ואחר כך שלח את הקובץ, ואני אשנה את השם שלו. "
        f"שים לב שאני יכול לשנות שמות קבצים עד <b>{humanize.naturalsize(MAX_FILE_SIZE)}</b>. 📁",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.private & filters.text)
async def set_file_name(_, message: Message):
    u_id = str(message.chat.id)
    if validate_file_name(message.text):
        file_names_shelve[u_id] = message.text
        await message.reply("יופי. עכשיו שלח את הקובץ.")
    else:
        await message.reply("נא להשתמש בשם תקין דוגמא\n <code>new_file.json</code>")


@app.on_message(filters.document & filters.private)
async def rename_file(client: Client, message: Message):
    u_id = str(message.chat.id)
    file_name = file_names_shelve.get(u_id, None)
    if file_name:
        if file_name == message.document.file_name:
            await message.reply("השם החדש זהה לשם הקובץ הנוכחי.")
            return
        if message.document.file_size > MAX_FILE_SIZE:
            await message.reply(f"הקובץ הזה גדול מהגודל המרבי המותר של {MAX_FILE_SIZE // (1024 * 1024)} מ\"ב.")
        else:
            progress_message = await message.reply("מוריד את הקובץ...")
            start_time = time.time()
            file_path = await message.download(message.document.file_id, progress=progress,
                                               progress_args=(client, progress_message, start_time))
            await progress_message.edit_text("מעלה את הקובץ...")
            await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
            await client.send_document(message.chat.id, file_path, file_name=file_name, progress=progress,
                                       progress_args=(client, progress_message, start_time), caption=f"הועלה על ידי {client.me.mention}\nעבור: {message.from_user.mention}")
            os.remove(file_path)
            await progress_message.delete()
        del file_names_shelve[u_id]
    else:
        await message.reply("אנא שלח את השם החדש לקובץ, ולאחר מכן שלח את הקובץ שוב.")


if __name__ == '__main__':
    app.run()
    file_names_shelve.close()
