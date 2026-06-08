import os
import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
from messages import WELCOME_TEXT

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- YAHAN APNE 200 SAWAAL PASTE KARO ---
# Dhyan rahe ki har line comma (,) se alag ho
QUIZ_DATA = [
    {"q": "2 + 2 = ?", "o": ["3", "4", "5", "6"], "a": 1},
    {"q": "Sahi spelling: Apple", "o": ["Apel", "Apple", "Appel", "Aple"], "a": 1},
    # Yahan apne saare 200 sawaal paste kar dena
    {"q": "Devil ki sahi spelling?", "o": ["Dival", "Devil", "Devel", "Devill"], "a": 1}
]
# ----------------------------------------

GROUP_GAMES = {}

@dp.message(Command("start"))
async def send_welcome_profile(message: types.Message):
    user_name = message.from_user.first_name.upper() if message.from_user.first_name else "PLAYER"
    await message.answer(WELCOME_TEXT.format(user_name=user_name))

@dp.message(Command("sp"))
async def change_quiz_speed(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Sahi tareeqa: /sp 10")
        return
    num_match = re.search(r'\d+', args[1])
    if num_match:
        new_time = int(num_match.group())
        GROUP_GAMES[message.chat.id] = GROUP_GAMES.get(message.chat.id, {"active": False, "speed": 15})
        GROUP_GAMES[message.chat.id]["speed"] = new_time
        await message.answer(f"⚡ Speed Updated: {new_time}s")

@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/on'))
async def start_native_quiz(message: types.Message):
    chat_id = message.chat.id
    game = GROUP_GAMES.get(chat_id, {"active": False, "speed": 15})
    if game["active"]:
        await message.answer("⚠️ Quiz pehle se chal raha hai!")
        return
    game["active"] = True
    GROUP_GAMES[chat_id] = game
    
    round_questions = random.sample(QUIZ_DATA, min(len(QUIZ_DATA), 15))
    await message.answer("🚀 QUIZ STARTING!")
    
    for idx, q_item in enumerate(round_questions):
        if not GROUP_GAMES[chat_id]["active"]: break
        await bot.send_poll(chat_id, f"Sawaal {idx+1}: {q_item['q']}", q_item["o"], 
                            type="quiz", correct_option_id=q_item["a"], open_period=game["speed"])
        await asyncio.sleep(game["speed"] + 1)
    GROUP_GAMES[chat_id]["active"] = False

@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/off'))
async def stop_native_quiz(message: types.Message):
    if message.chat.id in GROUP_GAMES:
        GROUP_GAMES[message.chat.id]["active"] = False
    await message.answer("🛑 Quiz rok diya gaya hai.")

async def handle_webhook(request):
    data = await request.json()
    await dp.feed_update(bot, types.Update(**data))
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    if RENDER_URL: await bot.set_webhook(url=f"{RENDER_URL}/webhook")
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000))).start()
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.r
      un(main())
