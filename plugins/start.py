# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on Telegram @CodeflixSupport

import asyncio
import time
import random
import string
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import *
from database.database import *

# File auto-delete time (Set your desired time in seconds)
FILE_AUTO_DELETE = TIME  
TUT_VID = f"{TUT_VID}"

@Bot.on_message(filters.command('start') & filters.private & subscribed1 & subscribed2 & subscribed3 & subscribed4)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if user is admin (Admins don't need verification)
    if user_id in ADMINS:
        verify_status = {
            'is_verified': True,
            'verify_token': None,
            'verified_time': time.time(),
            'link': ""
        }
    else:
        verify_status = await get_verify_status(user_id)

        if TOKEN:
            # Expire old tokens if needed
            if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
                await update_verify_status(user_id, is_verified=False)

            # Handle token verification
            if "verify_" in message.text:
                _, token = message.text.split("_", 1)
                if verify_status['verify_token'] != token:
                    return await message.reply("Your token is invalid or expired. Click /start to try again.")
                
                await update_verify_status(user_id, is_verified=True, verified_time=time.time())
                return await message.reply(
                    f"Your token is verified! It's valid for {get_exp_time(VERIFY_EXPIRE)}.",
                    protect_content=False,
                    quote=True
                )

            # Generate new token if not verified
            if not verify_status['is_verified']:
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                await update_verify_status(user_id, verify_token=token, link="")
                link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
                
                btn = [
                    [InlineKeyboardButton("• Open Link •", url=link)],
                    [InlineKeyboardButton('• How to Open Link •', url=TUT_VID)]
                ]
                return await message.reply(
                    f"<b>Your token has expired. Please refresh it.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\n"
                    "Pass 1 ad to use the bot for 23 hours without ads!</b>",
                    reply_markup=InlineKeyboardMarkup(btn),
                    protect_content=False,
                    quote=True
                )

    # Handle file retrieval process
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            decoded_string = await decode(base64_string)
            argument = decoded_string.split("-")
        except IndexError:
            return

        ids = []
        try:
            if len(argument) == 3:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            elif len(argument) == 2:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
        except Exception as e:
            print(f"Error decoding IDs: {e}")
            return

        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        sent_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption=msg.caption.html if msg.caption else "", 
                                             filename=msg.document.file_name) if CUSTOM_CAPTION and msg.document
                       else (msg.caption.html if msg.caption else ""))

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            protect_content=PROTECT_CONTENT)
                sent_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            protect_content=PROTECT_CONTENT)
                sent_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")

        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"<b>This file will be deleted in {get_exp_time(FILE_AUTO_DELETE)}. Save it before it's gone!</b>"
            )
            await asyncio.sleep(FILE_AUTO_DELETE)

            for msg in sent_msgs:    
                if msg:
                    try:    
                        await msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {msg.id}: {e}")

            await notification_msg.edit("<b>Your file has been deleted! Click below to retrieve it.</b>",
                                        reply_markup=InlineKeyboardMarkup(
                                            [[InlineKeyboardButton("Get File Again!", url=f"https://t.me/{client.username}?start={message.command[1]}")]]
                                        ))
    else:
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=f'@{message.from_user.username}' if message.from_user.username else None,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡️ About", callback_data="about")]])
        )

# Broadcast Function for Admins
@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

        pls_wait = await message.reply("<i>Broadcasting...</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
            total += 1

        status = f"""<b><u>Broadcast Complete</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        await pls_wait.edit(status)
    else:
        msg = await message.reply("<code>Reply to a message to broadcast.</code>")
        await asyncio.sleep(8)
        await msg.delete()
            
