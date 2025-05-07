import os
from aiogram import Router
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from create_bot import OXFORD_APP_ID, OXFORD_APP_KEY, YANDEX_API_KEY
import requests
from googletrans import Translator
import json

oxford_router = Router()
translator = Translator()

async def translate_to_russian(text: str) -> str:
    try:
        result = translator.translate(text, src='en', dest='ru')
        return result.text
    except Exception as e:
        print(f"Ошибка перевода: {str(e)}")
        return text

# Поиск определения слова
async def get_word_definition(word: str) -> str:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            definition = data[0]["meanings"][0]["definitions"][0]["definition"]
            translated = await translate_to_russian(definition)
            
            return (
                f"📖 **{word.capitalize()}**:\n"
                f"🇬🇧 {definition}\n"
                f"🇷🇺 {translated}"
            )
        return f"❌ Слово '{word}' не найдено в словаре."
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)}"

# Команда /define
@oxford_router.message(Command("define"))
async def define_word(message: types.Message):
    # Получаем слово после команды
    word = message.text.replace('/define', '').strip()
    
    if not word:
        await message.answer("ℹ️ Укажите слово после команды\nПример: /define hello")
        return
    
    definition = await get_word_definition(word)
    await message.answer(definition, parse_mode="Markdown")

# Обработка обычных сообщений
@oxford_router.message()
async def handle_other_messages(message: types.Message):
    await message.answer("ℹ️ Используйте команду /define <слово>")
