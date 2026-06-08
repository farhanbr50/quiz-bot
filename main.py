import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Token Verification
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Simple Questions Database
QUIZ_DATA = {
    "science": [
        {"q": "Pani (Water) ka chemical formula kya hai?", "o": ["H2O", "CO2", "O2", "NaCl"], "a": "H2O"},
        {"q": "Insaan ke jism mein kitni haddiyan (bones) hoti hain?", "o": ["201", "206", "208", "210"], "a": "206"}
    ],
    "movies": [
        {"q": "Sholay film mein Gabbar Singh ka role kisne kiya tha?", "o": ["Amitabh Bachchan", "Amjad Khan", "Dharmendra", "Sanjeev Kumar"], "a": "Amjad Khan"},
        {"q": "Bahubali director ka naam kya hai?", "o": ["S.S. Rajamouli", "Karan Johar", "Anurag Kashyap", "Rohit Shetty"], "a": "S.S. Rajamouli"}
    ],
    "gk": [
        {"q": "India ki capital (rajdhani) kaunsi hai?", "o": ["Mumbai", "Kolkata", "New Delhi", "Chennai"], "a": "New Delhi"},
        {"q": "Duniya ka sabse bada samundar (ocean) kaunsa hai?", "o": ["Indian Ocean", "Pacific Ocean", "Atlantic Ocean", "Arctic Ocean"], "a": "Pacific Ocean"}
    ],
    "tech": [
        {"q": "Python kya hai?", "o": ["Programming Language", "Snake", "Game", "Browser"], "a": "Programming Language"},
        {"q": "iPhone kis company ka product hai?", "o": ["Samsung", "Apple", "Google", "Mi"], "a": "Apple"}
    ]
}

USER_STATES = {}

# Start Command
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_name = message.from_user.first_name.upper()
    
    welcome_text = (
        f"╔════════════════════════╗\n"
        f"       WELCOME, {user_name}! 👋\n"
        f"╚════════════════════════╝\n\n"
        f"Hello {message.from_user.first_name}!\n"
        f"Niche diye gaye buttons se apni pasand ki category chuno aur quiz khelo:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📚 Science", callback_data="cat_science"))
    builder.row(types.InlineKeyboardButton(text="🎬 Movies", callback_data="cat_movies"))
    builder.row(types.InlineKeyboardButton(text="💡 GK", callback_data="cat_gk"))
    builder.row(types.InlineKeyboardButton(text="💻 Tech", callback_data="cat_tech"))
    
    await message.answer(welcome_text, reply_markup=builder.as_markup())

# Category Selection
@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def select_category(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    USER_STATES[user_id] = {
        "category": category,
        "current_index": 0,
        "score": 0
    }
    
    await send_question(callback.message, user_id)
    await callback.answer()

# Send Question Logic
async def send_question(message: types.Message, user_id: int):
    state = USER_STATES[user_id]
    category = state["category"]
    idx = state["current_index"]
    
    questions = QUIZ_DATA[category]
    
    if idx < len(questions):
        q_item = questions[idx]
        text = f"Sawaal {idx + 1}:\n\n{q_item['q']}"
        
        builder = InlineKeyboardBuilder()
        for option in q_item["o"]:
            builder.row(types.InlineKeyboardButton(text=option, callback_data=f"ans_{option}"))
            
        await message.edit_text(text, reply_markup=builder.as_markup())
    else:
        score = state["score"]
        total = len(questions)
        await message.edit_text(
            f"🏁 **QUIZ KHATAM!**\n\n"
            f"Tumhara Final Score: **{score}/{total}**\n\n"
            f"Dubara khelne ke liye /start dabayein."
        )
        USER_STATES.pop(user_id, None)

# Answer Handling
@dp.callback_query(lambda c: c.data.startswith("ans_"))
async def handle_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in USER_STATES:
        await callback.answer("Purana game hai, /start dabayein.", show_alert=True)
        return
        
    selected_ans = callback.data.split("_")[1]
    state = USER_STATES[user_id]
    category = state["category"]
    idx = state["current_index"]
    
    q_item = QUIZ_DATA[category][idx]
    
    if selected_ans == q_item["a"]:
        state["score"] += 1
        await callback.answer("✅ Sahi Jawab! Shabaash!")
    else:
        await callback.answer(f"❌ Galat Jawab! Sahi tha: {q_item['a']}", show_alert=True)
        
    state["current_index"] += 1
    await send_question(callback.message, user_id)

# Fake Web Server for Render Free Tier Port Binding
async def handle_web(request):
    return web.Response(text="Bot is running completely fine on Free Tier!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    await asyncio.gather(
        site.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
    
