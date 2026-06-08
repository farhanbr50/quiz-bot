import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Questions Database
QUIZ_DATA = [
    {"q": "Pani (Water) ka chemical formula kya hai?", "o": ["H2O", "CO2", "O2", "NaCl"], "a": "H2O"},
    {"q": "Insaan ke jism mein kitni haddiyan (bones) hoti hain?", "o": ["201", "206", "208", "210"], "a": "206"},
    {"q": "Sholay film mein Gabbar Singh ka role kisne kiya tha?", "o": ["Amitabh Bachchan", "Amjad Khan", "Dharmendra", "Sanjeev Kumar"], "a": "Amjad Khan"},
    {"q": "India ki capital (rajdhani) kaunsi hai?", "o": ["Mumbai", "Kolkata", "New Delhi", "Chennai"], "a": "New Delhi"},
    {"q": "iPhone kis company ka product hai?", "o": ["Samsung", "Apple", "Google", "Mi"], "a": "Apple"}
]

# Group Game State Storage
# Structure: { chat_id: { "current_index": 0, "scores": { user_id: { "name": name, "score": score } }, "answered_users": [], "msg_id": 123 } }
GROUP_GAMES = {}

# Start Command for Group
@dp.message(Command("start"))
async def start_group_quiz(message: types.Message):
    chat_id = message.chat.id
    
    # Check if game is already running in this group
    if chat_id in GROUP_GAMES:
        await message.answer("⚠️ Group mein pehle se ek quiz chal raha hai!")
        return

    # Initialize New Game for the Group
    GROUP_GAMES[chat_id] = {
        "current_index": 0,
        "scores": {},
        "answered_users": [],
        "msg_id": None
    }
    
    await message.answer("🎮 **GROUP MULTIPLAYER QUIZ SHURU HO RAHA HAI!** 🎮\n\nTaiyar ho jao sab log! 5 seconds mein pehla sawaal aa raha hai...")
    await asyncio.sleep(5)
    await send_group_question(chat_id)

# Function to Send Question to Group
async def send_group_question(chat_id: int):
    if chat_id not in GROUP_GAMES:
        return

    game = GROUP_GAMES[chat_id]
    idx = game["current_index"]
    
    if idx < len(QUIZ_DATA):
        q_item = QUIZ_DATA[idx]
        game["answered_users"] = [] # Reset answered list for new question
        
        text = f"❓ **SAWAAL {idx + 1}**:\n\n🔥 **{q_item['q']}**\n\n*Sab log jaldi jawab do!*"
        
        builder = InlineKeyboardBuilder()
        for option in q_item["o"]:
            builder.row(types.InlineKeyboardButton(text=option, callback_data=f"g_ans_{option}"))
            
        msg = await bot.send_message(chat_id, text, reply_markup=builder.as_markup())
        game["msg_id"] = msg.message_id
        
        # 15 seconds ka timer for each question
        await asyncio.sleep(15)
        await question_timeout(chat_id)
    else:
        await show_final_leaderboard(chat_id)

# Handler for Clicks (10-20 Users can click simultaneously)
@dp.callback_query(lambda c: c.data.startswith("g_ans_"))
async def handle_group_answer(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    if chat_id not in GROUP_GAMES:
        await callback.answer("Koi quiz active nahi hai.", show_alert=True)
        return
        
    game = GROUP_GAMES[chat_id]
    
    # Check if user already answered this question
    if user_id in game["answered_users"]:
        await callback.answer("Tumne is sawaal ka jawab pehle hi de diya hai! ❌", show_alert=True)
        return
        
    selected_ans = callback.data.split("g_ans_")[1]
    q_item = QUIZ_DATA[game["current_index"]]
    
    # Add to answered list so they can't click again
    game["answered_users"].append(user_id)
    
    # Initialize user score if not exists
    if user_id not in game["scores"]:
        game["scores"][user_id] = {"name": user_name, "score": 0}
        
    if selected_ans == q_item["a"]:
        game["scores"][user_id]["score"] += 1
        await callback.answer("✅ Sahi Jawab! Tumhe 1 point mila.")
    else:
        await callback.answer(f"❌ Galat Jawab! Sahi tha: {q_item['a']}")

# When 15 seconds are over
async def question_timeout(chat_id: int):
    if chat_id not in GROUP_GAMES:
        return
        
    game = GROUP_GAMES[chat_id]
    q_item = QUIZ_DATA[game["current_index"]]
    
    # Edit message to show correct answer and remove buttons
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=game["msg_id"],
            text=f"⏰ **TIME OUT!**\n\nSawaal: {q_item['q']}\n\n🟩 **Sahi Jawab Tha:** {q_item['a']}\n\nAgla sawaal 5 seconds mein..."
        )
    except Exception:
        pass
        
    await asyncio.sleep(5)
    game["current_index"] += 1
    await send_group_question(chat_id)

# Final Result & Leaderboard
async def show_final_leaderboard(chat_id: int):
    game = GROUP_GAMES[chat_id]
    scores = game["scores"]
    
    # Sort users by their highest score
    sorted_scores = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    
    result_text = "🏁 ═══ **QUIZ KHATAM!** ═══ 🏁\n\n🏆 **FINAL LEADERBOARD** 🏆\n\n"
    
    if not sorted_scores:
        result_text += "Kisi ne bhi quiz nahi khela! 🤷‍♂️"
    else:
        medals = ["🥇", "🥈", "🥉"]
        for rank, user_data in enumerate(sorted_scores):
            medal = medals[rank] if rank < 3 else "✨"
            result_text += f"{medal} **{user_data['name']}**: {user_data['score']} Points\n"
            
    await bot.send_message(chat_id, result_text)
    GROUP_GAMES.pop(chat_id, None) # Clear group game session

# Fake Web Server for Render
async def handle_web(request):
    return web.Response(text="Group Quiz Bot is Running Live!")

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
    
