import os
import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# 📥 Yahan hum messages.py se welcome text ko import kar rahe hain
from messages import WELCOME_TEXT

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 📝 VIP Questions Database
QUIZ_DATA = [
    {"q": "India ka National Animal (Rashtriya Pashu) kaun sa hai?", "o": ["Lion", "Tiger", "Leopard", "Elephant"], "a": "Tiger"},
    {"q": "Duniya ki sabse unchi choti (Highest Peak) kaunsi hai?", "o": ["K2", "Mount Everest", "Kangchenjunga", "Lhotse"], "a": "Mount Everest"},
    {"q": "Free Fire game kis company ne banaya hai?", "o": ["Tencent", "Garena", "Krafton", "Activision"], "a": "Garena"},
    {"q": "PUBG/BGMI mein ek squad mein max kitne players hote hain?", "o": ["2", "3", "4", "5"], "a": "4"},
    {"q": "Computer ka brain (dimaag) kise kaha jata hai?", "o": ["RAM", "CPU", "Hard Disk", "Monitor"], "a": "CPU"},
    {"q": "Social media app 'Instagram' ka owner kaun hai?", "o": ["Google", "Meta (Facebook)", "Microsoft", "Twitter"], "a": "Meta (Facebook)"},
    {"q": "Cricket mein ek over mein kitni valid balls hoti hain?", "o": ["4", "5", "6", "8"], "a": "6"},
    {"q": "Duniya ka sabse bada samundar (Largest Ocean) kaun sa hai?", "o": ["Indian Ocean", "Pacific Ocean", "Atlantic Ocean", "Arctic Ocean"], "a": "Pacific Ocean"},
    {"q": "YouTube par sabse pehla video kab upload hua tha?", "o": ["2005", "2006", "2007", "2008"], "a": "2005"},
    {"q": "Bitcoin kya hai?", "o": ["Gold", "Cryptocurrency", "Bank Share", "Paper Note"], "a": "Cryptocurrency"}
]

GROUP_GAMES = {}

# 🎮 Start Game
@dp.message(Command("start"))
async def start_premium_quiz(message: types.Message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name.upper()
    
    if chat_id in GROUP_GAMES:
        await message.answer("⚠️ Group mein pehle se ek game chal raha hai!")
        return

    GROUP_GAMES[chat_id] = {
        "current_index": 0,
        "scores": {},
        "correct_clicks": [],  
        "wrong_clicks": [],    
        "start_time": 0,
        "msg_id": None
    }
    
    # ⚡ messages.py se design load ho raha hai aur user ka naam fit ho raha hai
    text = WELCOME_TEXT.format(user_name=user_name)
    
    await message.answer(text)
    await asyncio.sleep(4)
    await send_vip_question(chat_id)

# ❓ Send Question
async def send_vip_question(chat_id: int):
    if chat_id not in GROUP_GAMES:
        return

    game = GROUP_GAMES[chat_id]
    idx = game["current_index"]
    
    if idx < len(QUIZ_DATA):
        q_item = QUIZ_DATA[idx]
        game["correct_clicks"] = []
        game["wrong_clicks"] = []
        game["start_time"] = time.time()
        
        text = (
            f"📊 ═══ **QUIZ BOT** ═══ 📊\n\n"
            f"❓ **SAWAAL {idx + 1}/{len(QUIZ_DATA)}**\n\n"
            f"🔥 👉 **{q_item['q']}**\n\n"
            f"⏱️ *Jaldi click karo! Speed points active hain!*"
        )
        
        builder = InlineKeyboardBuilder()
        for option in q_item["o"]:
            builder.row(types.InlineKeyboardButton(text=option, callback_data=f"v_ans_{option}"))
            
        msg = await bot.send_message(chat_id, text, reply_markup=builder.as_markup())
        game["msg_id"] = msg.message_id
    else:
        await show_final_leaderboard(chat_id)

# ⚡ Fast Click Handler
@dp.callback_query(lambda c: c.data.startswith("v_ans_"))
async def handle_vip_answer(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    if chat_id not in GROUP_GAMES:
        await callback.answer("Koi game active nahi hai.", show_alert=True)
        return
        
    game = GROUP_GAMES[chat_id]
    
    all_clicked_ids = [u.get("id") for u in game["correct_clicks"]] + [uid for uid in game["wrong_clicks"]]
    if user_id in all_clicked_ids:
        await callback.answer("Tumne is sawaal par pehle hi click kar diya hai! ❌", show_alert=True)
        return
        
    selected_ans = callback.data.split("v_ans_")[1]
    q_item = QUIZ_DATA[game["current_index"]]
    
    click_time = time.time() - game["start_time"]
    
    if selected_ans == q_item["a"]:
        # Pehle bande ko 120 points (Speed Bonus), baaki ko 50 points
        points = 120 if len(game["correct_clicks"]) == 0 else 50
        if click_time < 2.0 and points == 120:  
            points += 10 # Extra lightning fast bonus
            
        game["correct_clicks"].append({"id": user_id, "name": user_name, "points": points})
        
        if user_id not in game["scores"]:
            game["scores"][user_id] = {"name": user_name, "score": 0}
        game["scores"][user_id]["score"] += points
        
        await callback.answer(f"✅ Sahi Jawab! (+{points} pts)")
    else:
        game["wrong_clicks"].append(user_name)
        await callback.answer("❌ Galat Jawab! 0 points.")
        
    await update_live_message(chat_id)

# 🔄 Update Board Live
async def update_live_message(chat_id: int):
    game = GROUP_GAMES[chat_id]
    idx = game["current_index"]
    q_item = QUIZ_DATA[idx]
    
    correct_list = ", ".join([u["name"] for u in game["correct_clicks"]]) if game["correct_clicks"] else "No one yet"
    wrong_list = ", ".join(game["wrong_clicks"]) if game["wrong_clicks"] else "No one yet"
    
    text = (
        f"📊 ═══ **QUIZ BOT (LIVE)** ═══ 📊\n\n"
        f"❓ **SAWAAL {idx + 1}/{len(QUIZ_DATA)}**\n\n"
        f"🔥 👉 **{q_item['q']}**\n\n"
        f"🟩 **Sahi Jawab Wale:** {correct_list}\n"
        f"🟥 **Galat Jawab Wale:** {wrong_list}\n\n"
        f"🛑 Game locked! Agla sawaal lane ke liye niche button dabayein."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⏭️ Next Question", callback_data="vip_next"))
    
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=game["msg_id"], text=text, reply_markup=builder.as_markup())
    except Exception:
        pass

# ⏭️ Next Question Button
@dp.callback_query(lambda c: c.data == "vip_next")
async def go_to_next_question(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id not in GROUP_GAMES:
        return
        
    game = GROUP_GAMES[chat_id]
    q_item = QUIZ_DATA[game["current_index"]]
    
    try:
        await bot.send_message(chat_id, f"📢 Pichle sawaal ka sahi jawab tha: **{q_item['a']}**")
    except Exception:
        pass
        
    game["current_index"] += 1
    await send_vip_question(chat_id)

# 🏆 Final Leaderboard
async def show_final_leaderboard(chat_id: int):
    game = GROUP_GAMES[chat_id]
    scores = game["scores"]
    
    sorted_scores = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    
    result_text = "🏆 ════ **FINAL LEADERBOARD** ════ 🏆\n\n"
    
    if not sorted_scores:
        result_text += "Kisi ne sahi jawab nahi diya! 🤷‍♂️"
    else:
        medals = ["🥇", "🥈", "🥉"]
        for rank, user_data in enumerate(sorted_scores):
            medal = medals[rank] if rank < 3 else "✨"
            result_text += f"{medal} Rank {rank+1}: **{user_data['name']}** — `{user_data['score']}` pts\n"
            
    result_text += "\n🎮 Khelne ke liye shukriya! Naya game chalu karne ke liye `/start` likhein."
    await bot.send_message(chat_id, result_text)
    GROUP_GAMES.pop(chat_id, None)

# Fake Web Server for Render
async def handle_web(request):
    return web.Response(text="VIP Quiz Bot with External Messages is Running Live!")

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
    
