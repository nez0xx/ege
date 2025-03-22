import asyncio
from aiogram import Bot, Dispatcher

from Bot.config import BOT_TOKEN, db, description_1
from Bot.handlers.main_handlers import router as main_router
from Bot.handlers.options_handlers import router as admin_router, create_task
from Bot.handlers.owner_handlers import router as owner_router

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
dp.include_router(owner_router)
dp.include_router(admin_router)
dp.include_router(main_router)
db.off_timers()


async def startup():
    timers = db.get_all('timers')
    loop = asyncio.get_event_loop()
    for timer in timers:
        values = list(timer.values())
        db.set_timer(*values)
        loop.create_task(create_task(timer, bot))


async def main():
    startups = asyncio.create_task(startup())
    me = await bot.get_me()
    #db.add_reply(title='✅ Проверка подписки', description=description_1, photo=None, keyboard=f'[➕Добавить в группу](http://t.me/{me.username}?startgroup=new)')
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await startups

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass