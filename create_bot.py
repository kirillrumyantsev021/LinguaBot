from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import os


admins = []
TOKEN = "8008241574:AAEj7iOsZlAmE93uCqHHbmQdYTWN-jsbMc4"
OWNER_ID = 5049735374
OXFORD_APP_ID = "b16250b7"
OXFORD_APP_KEY = "95a25d1723e8c23f843d19e0ca8d8a2c"
YANDEX_API_KEY = "b1ggvdbqch5unse7tdv5"

all_media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_media')

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())