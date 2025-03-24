import asyncio
from aiohttp import web
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
from config import *
from plugins import web_server

# Bot Name Banner
BOT_BANNER = """
  ___ ___  ___  ___ ___ _    _____  _____  ___ _____ ___ 
 / __/ _ \\|   \\| __| __| |  |_ _\\ \\/ / _ )/ _ \\_   _/ __|
| (_| (_) | |) | _|| _|| |__ | | >  <| _ \\ (_) || | \\__ \\
 \\___\\___/|___/|___|_| |____|___/_/\\_\\___/\\___/ |_| |___/
                                                         
"""                                                                                     

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER
        self.uptime = None
        self.invitelinks = {}

    async def start(self):
        await super().start()
        self.uptime = datetime.now()
        usr_bot_me = await self.get_me()
        self.username = usr_bot_me.username

        # Force Subscribe Check
        for i, channel in enumerate([FORCE_SUB_CHANNEL1, FORCE_SUB_CHANNEL2, FORCE_SUB_CHANNEL3, FORCE_SUB_CHANNEL4], start=1):
            if channel:
                try:
                    chat = await self.get_chat(channel)
                    link = chat.invite_link or (await self.export_chat_invite_link(channel))
                    self.invitelinks[f"channel{i}"] = link
                except Exception as e:
                    self.LOGGER.warning(f"⚠️ Error in FORCE_SUB_CHANNEL{i}: {e}")
                    self.LOGGER.warning(f"Check if bot is an admin in {channel} with 'Invite via Link' permission!")
                    sys.exit()

        # Database Channel Check
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test_msg = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test_msg.delete()
        except Exception as e:
            self.LOGGER.warning(f"⚠️ Database Channel Error: {e}")
            self.LOGGER.warning(f"Check if bot is an admin in CHANNEL_ID {CHANNEL_ID}!")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER.info(f"✅ Bot Started! Made by @Codeflix_Bots")
        self.LOGGER.info(BOT_BANNER)

        # Start Web Server
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        # Notify Owner
        try:
            await self.send_message(OWNER_ID, text="<b>🤖 Bot Restarted by @Codeflix_Bots</b>")
        except Exception as e:
            self.LOGGER.warning(f"⚠️ Unable to send restart message to OWNER_ID: {e}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER.info("❌ Bot Stopped.")

    def run(self):
        """Start the bot event loop."""
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER.info("⚠️ Shutting Down Bot...")
        finally:
            loop.run_until_complete(self.stop())
         
