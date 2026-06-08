import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# messages.py se stylish welcome profile load hoga
from messages import WELCOME_TEXT

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔢 Quiz Data (Poll Format)
QUIZ_DATA = [
    {"q": "2 + 2 = ?", "o": ["3", "4", "5", "6"], "a": 1},       
    {"q": "5 + 7 = ?", "o": ["10", "11", "12", "13"], "a": 2},     
    {"q": "10 - 3 = ?", "o": ["6", "7", "8", "9"], "a": 1},       
    {"q": "4 x 2 = ?", "o": ["6", "8", "10", "12"], "a": 1},      
    {"q": "20 ÷ 2 = ?", "o": ["5", "10", "15", "20"], "a": 1}      
]

GROUP_GAMES = {}

# 1️⃣ /start karne par SIRF stylish welcome profile message aayega (Game Shuru nahi hoga)
@dp.message(Command("start"))
async def send_welcome_profile(message: types.Message):
    user_name = message.from_user.first_name.upper()
    text = WELCOME_TEXT.format(user_name=user_name)
    await message.answer(text)

# ⚙️ Speed Changer Command (/sc 10, /sc 20 etc.)
@dp.message(Command("sc"))
async def change_quiz_speed(message: types.Message):
    chat_id = message.chat.id
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("⚠️ **Sahi tareeqa:** `/sc 10` ya `/sc 20` likhein!")
        return
        
    try:
        new_time = int(args[1])
        if new_time < 5 or new_time > 300:
            await message.answer("⚠️ **Error:** Speed limit 5s se 300s tak hi ho sakti hai!")
            return
            
        if chat_id not in GROUP_GAMES:
            GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
            
        GROUP_GAMES[chat_id]["speed"] = new_time
        await message.answer(f"⚡ **Speed Changed Successfully!**\nAb se har sawaal **{new_time} Seconds** tak chalega.")
        
    except ValueError:
        await message.answer("⚠️ **Error:** `/sc` ke aage ek sahi number dalein!")

# 2️⃣ Quiz Shuru Karne Ka Command: /quiz/on
@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/on'))
async def start_native_quiz(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
        
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ **Group mein pehle se ek quiz chal raha hai!**")
        return

    GROUP_GAMES[chat_id]["active"] = True
    current_speed = GROUP_GAMES[chat_id]["speed"]
    
    await message.answer(f"🚀 **MATHS QUIZ BATTLE STARTING IN 3 SECONDS...**\n⏱️ *Speed Set:* **{current_speed}s per question!*")
    await asyncio.sleep(3)

    for idx, q_item in enumerate(QUIZ_DATA):
        # Agar beech mein /quiz/off kiya toh loop turant ruk jayega
        if chat_id not in GROUP_GAMES or not GROUP_GAMES[chat_id]["active"]:
            break
            
        # Telegram Polling Quiz
        await bot.send_poll(
            chat_id=chat_id,
            question=f"📝 SAWAAL {idx + 1}/{len(QUIZ_DATA)}:\n👉 {q_item['q']}",
            options=q_item["o"],
            type="quiz",
            correct_option_id=q_item["a"],
            is_anonymous=False,
            open_period=current_speed
        )
        
        await asyncio.sleep(current_speed + 1)

    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id]["active"]:
        await bot.send_message(chat_id, "🏁 **Quiz Khatam! Khelne ke liye sabhi ka shukriya. ✨**")
        GROUP_GAMES[chat_id]["active"] = False

# 3️⃣ Quiz Rokne Ka Command: /quiz/off
@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/off'))
async def stop_native_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id]["active"]:
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("🛑 **Quiz ko beech mein hi rok diya gaya hai!**\n\nNaya game shuru karne ke liye `/quiz/on` likhein.")
    else:
        await message.answer("⚠️ **Abhi group mein koi quiz nahi chal raha hai jise roka jaye!**")

# 🌐 Webhook Handler
async def handle_webhook(request):
    url = str(request.url)
    if "webhook" in url:
        request_data = await request.json()
        update = types.Update(**request_data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    return web.Response(text="Bot Live!")

async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/", handle_webhook)
    
    if RENDER_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(url=f"{RENDER_URL}/webhook")

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
