import os
import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Files ko import kar rahe hain
from welcome import get_welcome_text
from quiz_data import QUESTIONS  # NOTE: quiz_data.py mein 'QUESTIONS' list honi chahiye

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

GROUP_GAMES = {}

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_name = message.from_user.first_name.upper() if message.from_user.first_name else "PLAYER"
    await message.answer(get_welcome_text(user_name), parse_mode="Markdown")

@dp.message(Command("sp"))
async def change_quiz_speed(message: types.Message):
    args = message.text.split()
    if len(args) < 2: 
        await message.answer("❌ Usage: /sp <seconds> (e.g., /sp 15)")
        return
    num = re.search(r'\d+', args[1])
    if num:
        if message.chat.id not in GROUP_GAMES:
            GROUP_GAMES[message.chat.id] = {"active": False, "speed": 15}
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed Updated: {num.group()} seconds per question")
    else:
        await message.answer("❌ Please provide a valid number! Example: /sp 15")

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/on', '/quiz on'])
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
    
    game = GROUP_GAMES[chat_id]
    if game["active"]: 
        await message.answer("⚠️ Quiz already running!")
        return
    
    game["active"] = True
    GROUP_GAMES[chat_id] = game
    
    # quiz_data.py se QUESTIONS list use ho rahi hai
    if not QUESTIONS:
        await message.answer("❌ No questions available! Please contact admin.")
        game["active"] = False
        return
    
    round_questions = random.sample(QUESTIONS, min(len(QUESTIONS), 15))
    await message.answer("🚀 QUIZ STARTING! Get ready...")
    
    for idx, q in enumerate(round_questions):
        if not GROUP_GAMES[chat_id]["active"]: 
            break
        
        # Check if question has correct format
        if 'q' not in q or 'o' not in q or 'a' not in q:
            await message.answer(f"⚠️ Question {idx+1} has wrong format! Skipping...")
            continue
            
        await bot.send_poll(
            chat_id, 
            f"Question {idx+1}: {q['q']}", 
            q['o'], 
            type="quiz", 
            correct_option_id=int(q['a']),  # Ensure it's integer
            open_period=game["speed"]
        )
        await asyncio.sleep(game["speed"] + 1)
    
    game["active"] = False
    await message.answer("🏁 Quiz completed! Thanks for playing!")

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    if message.chat.id in GROUP_GAMES and GROUP_GAMES[message.chat.id]["active"]:
        GROUP_GAMES[message.chat.id]["active"] = False
        await message.answer("🛑 Quiz stopped by command!")
    else:
        await message.answer("❌ No active quiz to stop!")

async def handle_webhook(request):
    data = await request.json()
    await dp.feed_update(bot, types.Update(**data))
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    
    if RENDER_URL:
        await bot.set_webhook(url=f"{RENDER_URL}/webhook")
        print(f"✅ Webhook set to {RENDER_URL}/webhook")
    else:
        print("⚠️ No webhook URL set!")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()
    print(f"🚀 Bot is running on port {os.getenv('PORT', 10000)}")
    
    # Keep the bot running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
