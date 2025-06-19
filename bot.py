import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.utils.executor import start_webhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

API_TOKEN = '8195418513:AAGL24nsoxSg9Lmgi7m0GLnos4m6qh_oavY'
WEBHOOK_HOST = 'https://your-render-url.onrender.com'  # ЗАМЕНИ ПОТОМ
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 10000

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

USERS_FILE = 'users.json'
STEPS_FILE = 'steps.json'

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

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    scheduler.add_job(send_daily_steps, 'cron', hour=6, minute=0)
    scheduler.start()

async def on_shutdown(dp):
    await bot.delete_webhook()

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer("Напиши /start, чтобы начать получать задания.")

@dp.errors_handler()
async def global_error_handler(update: Update, exception):
    print(f"Ошибка: {exception}")
    return True

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
