import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_TOKEN = '7595275690:AAE1oL5nIOIaVWngbeP4FvSBTUSKrrnB8eE'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

USERS_FILE = 'users.json'
STEPS_FILE = 'steps.json'
TARGET_HOUR = 9  # по Москве (GMT+3)

with open(STEPS_FILE, 'r', encoding='utf-8') as f:
    steps = json.load(f)

def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"step": 0}
        save_users(users)
        await message.reply("Привет! Я буду отправлять тебе шаги по формулировке цели. Первое задание придёт завтра в 9:00 по Москве.")
    else:
        await message.reply("Ты уже подписан. Следующий шаг придёт по расписанию!")

async def send_daily_steps():
    users = load_users()
    updated = False
    for user_id, data in users.items():
        step_index = data["step"]
        if step_index < len(steps):
            try:
                await bot.send_message(int(user_id), steps[step_index])
                users[user_id]["step"] += 1
                updated = True
            except Exception as e:
                print(f"Ошибка при отправке пользователю {user_id}: {e}")
    if updated:
        save_users(users)

async def on_startup(_):
    scheduler.add_job(send_daily_steps, 'cron', hour=6, minute=0)  # 6:00 UTC = 9:00 MSK
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
