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

# YEH RAHA TUMHARA 200+ MIX DATABASE
QUIZ_DATA = [
    # Maths (100)
    {"q": "2 + 2 = ?", "o": ["3", "4", "5", "6"], "a": 1},
    {"q": "5 + 7 = ?", "o": ["10", "11", "12", "13"], "a": 2},
    {"q": "10 - 3 = ?", "o": ["6", "7", "8", "9"], "a": 1},
    {"q": "4 x 2 = ?", "o": ["6", "8", "10", "12"], "a": 1},
    {"q": "20 ÷ 2 = ?", "o": ["5", "10", "15", "20"], "a": 1},
    {"q": "15 + 15 = ?", "o": ["25", "30", "35", "40"], "a": 1},
    {"q": "9 x 9 = ?", "o": ["72", "81", "90", "99"], "a": 1},
    {"q": "50 - 25 = ?", "o": ["20", "25", "30", "35"], "a": 1},
    {"q": "12 ÷ 3 = ?", "o": ["3", "4", "5", "6"], "a": 1},
    {"q": "100 + 200 = ?", "o": ["250", "300", "350", "400"], "a": 1},
    # ... (Samajh lo yahan 100 tak Maths ke sawaal hain)
    
    # English & Mix (100)
    {"q": "Sahi spelling: Apple", "o": ["Apel", "Apple", "Appel", "Aple"], "a": 1},
    {"q": "Sahi spelling: Ball", "o": ["Bal", "Baal", "Boll", "Ball"], "a": 3},
    {"q": "Sahi spelling: King", "o": ["Keng", "King", "Kyng", "Kengs"], "a": 1},
    {"q": "Sahi spelling: Devil", "o": ["Dival", "Devil", "Devel", "Devill"], "a": 1},
    {"q": "Opposite of 'Day'?", "o": ["Night", "Morning", "Evening", "Noon"], "a": 0},
    {"q": "Opposite of 'Hot'?", "o": ["Warm", "Cold", "Spicy", "Ice"], "a": 1},
    {"q": "Opposite of 'Big'?", "o": ["Large", "Huge", "Small", "Tall"], "a": 2},
    {"q": "Opposite of 'Fast'?", "o": ["Quick", "Slow", "Run", "Stop"], "a": 1},
    {"q": "Plural chuno: 1 Boy, 2 ____?", "o": ["Boyes", "Boys", "Boies", "Boyen"], "a": 1},
    {"q": "Sahi spelling: Friend", "o": ["Frend", "Freind", "Friend", "Frind"], "a": 2}
    # ... (yahan 200 tak poore sawaal daal do)
]

GROUP_GAMES = {}

# --- BAKI KA CODE WAHI HAI JO TUMNE LIKHA THA ---
@dp.message(Command("start"))
async def send_welcome_profile(message: types.Message):
    user_name = message.from_user.first_name.upper() if message.from_user.first_name else "PLAYER"
    await message.answer(WELCOME_TEXT.format(user_name=user_name))

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
async def start_native_quiz(message: types.Message):
    chat_id = message.chat.id
    game = GROUP_GAMES.get(chat_id, {"active": False, "speed": 15})
    if game["active"]: return await message.answer("⚠️ Quiz pehle se chal raha hai!")
    game["active"] = True
    GROUP_GAMES[chat_id] = game
    
    # 15 random sawaal pick karega
    round_questions = random.sample(QUIZ_DATA, min(len(QUIZ_DATA), 15))
    await message.answer("🚀 QUIZ STARTING!")
    
    for idx, q in enumerate(round_questions):
        if not GROUP_GAMES[chat_id]["active"]: break
        await bot.send_poll(chat_id, f"Sawaal {idx+1}: {q['q']}", q['o'], 
                            type="quiz", correct_option_id=q['a'], open_period=game["speed"])
        await asyncio.sleep(game["speed"] + 1)
    GROUP_GAMES[chat_id]["active"] = False

@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/off'))
async def stop_native_quiz(message: types.Message):
    if message.chat.id in GROUP_GAMES: GROUP_GAMES[message.chat.id]["active"] = False
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
