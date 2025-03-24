import asyncio
import sys
import logging
from datetime import datetime
from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode
import pyromod.listen
from config import API_HASH, APP_ID, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL1, FORCE_SUB_CHANNEL2, FORCE_SUB_CHANNEL3, FORCE_SUB_CHANNEL4, CHANNEL_ID, OWNER_ID, PORT
from plugins import web_server

# Configure Logger
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

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

    async def start(self):
        await super().start()
        self.uptime = datetime.now()
        self.username = (await self.get_me()).username

        self.LOGGER.info("✅ Bot Started! Made by @Codeflix_Bots")

        # Check force subscription channels
        await self.check_force_sub_channel(FORCE_SUB_CHANNEL1, "FORCE_SUB_CHANNEL1")
        await self.check_force_sub_channel(FORCE_SUB_CHANNEL2, "FORCE_SUB_CHANNEL2")
        await self.check_force_sub_channel(FORCE_SUB_CHANNEL3, "FORCE_SUB_CHANNEL3")
        await self.check_force_sub_channel(FORCE_SUB_CHANNEL4, "FORCE_SUB_CHANNEL4")

        # Check DB Channel
        await self.check_db_channel()

        # Start Web Server
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        # Notify Owner
        try:
            await self.send_message(OWNER_ID, text=f"<b>🤖 Bot Restarted by @Codeflix_Bots</b>")
        except Exception as e:
            self.LOGGER.warning(f"Failed to send start notification: {e}")

    async def check_force_sub_channel(self, channel_id, var_name):
        if not channel_id:
            return
        try:
            chat = await self.get_chat(channel_id)
            link = chat.invite_link or await self.export_chat_invite_link(channel_id)
            setattr(self, f"invitelink_{var_name.lower()[-1]}", link)
        except Exception as e:
            self.LOGGER.warning(f"❌ Cannot get invite link for {var_name}: {e}")
            self.LOGGER.warning(f"Make sure the bot is an admin with 'Invite Users via Link' permission in {var_name} ({channel_id}).")
            sys.exit()

    async def check_db_channel(self):
        try:
            self.db_channel = await self.get_chat(CHANNEL_ID)
            test_msg = await self.send_message(self.db_channel.id, "Test Message")
            await test_msg.delete()
        except Exception as e:
            self.LOGGER.warning(f"❌ DB Channel Error: {e}")
            self.LOGGER.warning(f"Make sure the bot is an admin in the DB Channel ({CHANNEL_ID}).")
            sys.exit()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER.info("❌ Bot Stopped.")

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER.info("🔴 Shutting down...")
        finally:
            loop.run_until_complete(self.stop())

# Start the bot
if __name__ == "__main__":
    Bot().run()
                                
