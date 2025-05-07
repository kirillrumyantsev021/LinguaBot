import asyncio
import logging
from create_bot import bot, dp
from handlers.Oxford_api import oxford_router
from handlers.cards import cards_router


logging.basicConfig(level=logging.INFO)

async def main():
    # dp.middleware.setup(LoggingMiddleware())
    
    dp.include_router(cards_router)
    dp.include_router(oxford_router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())