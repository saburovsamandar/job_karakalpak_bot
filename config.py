import os
from dotenv import load_dotenv
load_dotenv()

BotToken = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_USERNAME")
ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))

