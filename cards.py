import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os

cards_router = Router()

def init_db():
    with sqlite3.connect('flashcards.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS flashcards
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         word TEXT NOT NULL,
                         translation TEXT NOT NULL,
                         example TEXT,
                         user_id INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_progress
                         (user_id INTEGER,
                         word_id INTEGER,
                         status TEXT,
                         last_reviewed TEXT)''')
        conn.commit()

init_db()

# Команда /cards - главное меню
@cards_router.message(Command("cards"))
async def cards_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать обучение", callback_data="start_cards")],
        [InlineKeyboardButton(text="➕ Добавить карточку", callback_data="add_card_menu")]
    ])
    await message.answer("📇 Режим карточек", reply_markup=keyboard)

# Начало тренировки
@cards_router.callback_query(F.data == "start_cards")
async def start_flashcards(callback: CallbackQuery):
    conn = sqlite3.connect('flashcards.db')
    cursor = conn.cursor()
    
    # Берем случайную карточку, которую пользователь еще не знает
    cursor.execute('''SELECT word FROM flashcards 
                      WHERE id NOT IN 
                      (SELECT word_id FROM user_progress 
                       WHERE user_id = ? AND status = 'known')
                      ORDER BY RANDOM() LIMIT 1''', 
                  (callback.from_user.id,))
    
    word = cursor.fetchone()
    conn.close()
    
    if not word:
        await callback.message.edit_text("🎉 Вы изучили все карточки!\nДобавьте новые через /add_card")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Показать перевод", callback_data=f"reveal_{word[0]}")]
    ])
    
    await callback.message.edit_text(
        f"🔤 Слово: <b>{word[0]}</b>\n\n"
        f"ℹ️ Нажмите кнопку чтобы увидеть перевод",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Раскрытие перевода
@cards_router.callback_query(F.data.startswith("reveal_"))
async def reveal_translation(callback: CallbackQuery):
    word = callback.data.split("_")[1]
    
    with sqlite3.connect('flashcards.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT translation, example, id FROM flashcards WHERE word=?", (word,))
        result = cursor.fetchone()
    
    if not result:
        await callback.answer("Карточка не найдена!")
        return
    
    translation, example, card_id = result
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Знаю", callback_data=f"know_{card_id}")],
        [InlineKeyboardButton(text="🔄 Повторить", callback_data=f"repeat_{card_id}")],
        [InlineKeyboardButton(text="➡️ Следующая", callback_data="next_card")]
    ])
    
    response = f"🔤 <b>{word}</b>\n\n🇷🇺 {translation}"
    if example:
        response += f"\n\n📝 Пример:\n{example}"
    
    await callback.message.edit_text(
        response,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Обработка ответов
@cards_router.callback_query(F.data.startswith("know_"))
async def mark_as_known(callback: CallbackQuery):
    card_id = callback.data.split("_")[1]
    
    with sqlite3.connect('flashcards.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO user_progress 
                          (user_id, word_id, status) 
                          VALUES (?, ?, ?)''',
                      (callback.from_user.id, card_id, 'known'))
        conn.commit()
    
    await callback.answer("Добавлено в изученные!")
    await next_card(callback)

@cards_router.callback_query(F.data.startswith("repeat_"))
async def mark_for_repeat(callback: CallbackQuery):
    card_id = callback.data.split("_")[1]
    
    with sqlite3.connect('flashcards.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO user_progress 
                          (user_id, word_id, status) 
                          VALUES (?, ?, ?)''',
                      (callback.from_user.id, card_id, 'repeat'))
        conn.commit()
    
    await callback.answer("Добавлено в повторение!")
    await next_card(callback)

@cards_router.callback_query(F.data == "next_card")
async def next_card(callback: CallbackQuery):
    await start_flashcards(callback)

# Добавление карточек
@cards_router.callback_query(F.data == "add_card_menu")
async def add_card_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "✏️ Отправьте новую карточку в формате:\n"
        "<слово>|<перевод>[|пример]\n\n"
        "Например:\n"
        "cat|кот\n"
        "или\n"
        "dog|собака|The dog barks - Собака лает"
    )

@cards_router.message(F.text.contains("|"))
async def process_new_card(message: types.Message):
    try:
        parts = message.text.split("|")
        word = parts[0].strip()
        translation = parts[1].strip()
        example = parts[2].strip() if len(parts) > 2 else None
        
        with sqlite3.connect('flashcards.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO flashcards (word, translation, example, user_id) VALUES (?, ?, ?, ?)",
                (word, translation, example, message.from_user.id)
            )
            conn.commit()
        
        await message.answer(f"✅ Карточка добавлена:\n<b>{word}</b> - {translation}", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}\nПроверьте формат ввода!")