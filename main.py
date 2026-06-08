import os
import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Files ko import kar rahe hain
from welcome import get_welcome_text
from quiz_data import QUESTIONS 

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

GROUP_GAMES = {}

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_name = message.from_user.first_name.upper() if message.from_user.first_name else "PLAYER"
    # welcome.py se text utha raha hai
    await message.answer(get_welcome_text(user_name), parse_mode="Markdown")

@dp.message(Command("sp"))
async def change_quiz_speed(message: types.Message):
    args = message.text.split()
    if len(args) < 2: return
    num = re.search(r'\d+', args[1])
    if num:
        GROUP_GAMES[message.chat.id] = GROUP_GAMES.get(message.chat.id, {"active": False, "speed": 15})
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed Updated: {num.group()}s")

@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/on'))
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    game = GROUP_GAMES.get(chat_id, {"active": False, "speed": 15})
    if game["active"]: return await message.answer("⚠️ Quiz pehle se chal raha hai!")
    game["active"] = True
    GROUP_GAMES[chat_id] = game
    
    # quiz_data.py se QUESTIONS list use ho rahi hai
    round_questions = random.sample(QUESTIONS, min(len(QUESTIONS), 15))
    await message.answer("🚀 QUIZ STARTING!")
    
    for idx, q in enumerate(round_questions):
        if not GROUP_GAMES[chat_id]["active"]: break
        await bot.send_poll(chat_id, f"Sawaal {idx+1}: {q['q']}", q['o'], 
                            type="quiz", correct_option_id=q['a'], open_period=game["speed"])
        await asyncio.sleep(game["speed"] + 1)
    GROUP_GAMES[chat_id]["active"] = False

@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/off'))
async def stop_quiz(message: types.Message):
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
    asyncio.
    run(main())
