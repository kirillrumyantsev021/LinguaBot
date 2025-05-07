import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import logging
from create_bot import logger
from datetime import datetime

goal_router = Router()

def init_db():
    try:
        with sqlite3.connect('flashcards.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_goals
                            (user_id INTEGER PRIMARY KEY,
                             target_words INTEGER,
                             start_date TEXT,
                             deadline TEXT)''')
            conn.commit()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")

@goal_router.message(Command("setgoal"))
async def set_goal_command(message: types.Message):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "Используйте формат:\n"
            "<code>/setgoal количество_слов</code>\n\n"
            "Пример:\n"
            "<code>/setgoal 50</code> - цель 50 слов",
            parse_mode="HTML"
        )
        return
    
    target = int(args[1])
    with sqlite3.connect('flashcards.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO user_goals 
                        (user_id, target_words, start_date)
                        VALUES (?, ?, ?)''',
                    (message.from_user.id, target, datetime.now().date().isoformat()))
        conn.commit()
    
    await message.answer(
        f"🎯 Цель установлена: выучить <b>{target}</b> слов!\n"
        "Отслеживайте прогресс в разделе статистики.",
        parse_mode="HTML"
    )

@goal_router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    try:
        with sqlite3.connect('flashcards.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM flashcards")
            total = cursor.fetchone()[0]
            
            cursor.execute('''SELECT COUNT(*) FROM user_progress 
                            WHERE user_id = ? AND status = 'known' ''',
                        (callback.from_user.id,))
            known = cursor.fetchone()[0]
            
            cursor.execute('''SELECT target_words, start_date FROM user_goals
                            WHERE user_id = ?''',
                        (callback.from_user.id,))
            goal_data = cursor.fetchone()
            
            goal_info = ""
            if goal_data:
                target, start_date = goal_data
                progress_percent = min(100, round(known/target*100))
                goal_info = (
                    f"\n\n🎯 Цель: {known}/{target} слов\n"
                    f"📈 Прогресс: {progress_percent}%\n"
                    f"⏳ Дата начала: {start_date}"
                )
                
                filled = '🟩' * (progress_percent // 10)
                empty = '⬜' * (10 - (progress_percent // 10))
                goal_info += f"\n{filled}{empty}"
            else:
                goal_info = "\n\n🎯 Цель не установлена."

        stats_message = (
            f"📊 Ваша статистика:\n\n"
            f"• Всего карточек: {total}\n"
            f"• Изучено: {known}\n"
            f"{goal_info}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Установить цель", callback_data="set_goal")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ])

        await callback.message.edit_text(
            stats_message,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")

@goal_router.callback_query(F.data == "set_goal")
async def set_goal_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введите количество слов, которое хотите выучить:\n\n"
        "Пример: <code>50</code> - цель 50 слов",
        parse_mode="HTML"
    )
    await callback.answer()

@goal_router.message(lambda message: message.text.isdigit() and len(message.text) < 5)
async def process_goal_input(message: types.Message):
    target = int(message.text)
    with sqlite3.connect('flashcards.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO user_goals 
                        (user_id, target_words, start_date)
                        VALUES (?, ?, ?)''',
                    (message.from_user.id, target, datetime.now().date().isoformat()))
        conn.commit()
    
    await message.answer(
        f"🎯 Цель установлена: выучить <b>{target}</b> слов!\n"
        "Проверить прогресс можно в разделе статистики (/stats).",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Посмотреть статистику", callback_data="stats")]
        ])
    )