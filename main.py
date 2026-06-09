import os
import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

from welcome import get_welcome_text
from questions import get_random_questions

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
            GROUP_GAMES[message.chat.id] = {"active": False, "speed": 15, "scores": {}, "wrong": {}}
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed set to {num.group()} seconds per question!")
    else:
        await message.answer("❌ Invalid number! Example: /sp 15")

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/on', '/quiz on'])
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15, "scores": {}, "wrong": {}}
    
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ Quiz already running! Use /quiz off to stop.")
        return
    
    total_qs = 30  # 30 questions per quiz
    
    GROUP_GAMES[chat_id] = {
        "active": True,
        "speed": GROUP_GAMES[chat_id].get("speed", 15),
        "scores": {},
        "wrong": {},
        "current_question": 0,
        "total_questions": total_qs
    }
    
    selected_questions = get_random_questions(total_qs)
    GROUP_GAMES[chat_id]["questions"] = selected_questions
    
    await message.answer(
        f"🌸💖✨ **MAHAKAL QUIZ** ✨💖🌸\n"
        f"╔════════════════════════════════╗\n"
        f"║     🎯 QUIZ STARTING 🎯        ║\n"
        f"╚════════════════════════════════╝\n\n"
        f"📚 **Total Questions:** {GROUP_GAMES[chat_id]['total_questions']}\n"
        f"⏱️ **Time per Question:** {GROUP_GAMES[chat_id]['speed']} seconds\n\n"
        f"💪 **Chalo Shuru Karte Hain!**\n"
        f"🌸 **Best of Luck!** 🌸"
    )
    
    await send_question(chat_id)

async def send_question(chat_id):
    game = GROUP_GAMES.get(chat_id)
    if not game or not game["active"]:
        return
    
    idx = game["current_question"]
    questions = game["questions"]
    
    if idx >= len(questions):
        await end_quiz(chat_id)
        return
    
    q = questions[idx]
    
    question_text = (
        f"🌸💖✨ **MAHAKAL QUIZ** ✨💖🌸\n"
        f"┌────────────────────────────────────┐\n"
        f"│  📍 **Q{idx+1}/{game['total_questions']}**\n"
        f"│\n"
        f"│  🎯 {q['q']}\n"
        f"│\n"
        f"│  ⏱️ **Time:** {game['speed']} seconds\n"
        f"└────────────────────────────────────┘"
    )
    
    poll_message = await bot.send_poll(
        chat_id,
        question_text,
        q['o'],
        type="quiz",
        correct_option_id=int(q['a']),
        open_period=game["speed"]
    )
    
    game["current_poll_id"] = poll_message.poll.id
    game["current_question_data"] = q
    
    await asyncio.sleep(game["speed"] + 1)
    
    game["current_question"] += 1
    await send_question(chat_id)

@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    for chat_id, game in GROUP_GAMES.items():
        if not game.get("active"):
            continue
        
        if game.get("current_poll_id") == poll_answer.poll_id:
            user_id = poll_answer.user.id
            user_name = poll_answer.user.first_name or "Unknown"
            
            current_q = game.get("current_question_data")
            if current_q:
                correct_answer = int(current_q['a'])
                user_answer = poll_answer.option_ids[0] if poll_answer.option_ids else -1
                
                if user_answer == correct_answer:
                    if user_id not in game["scores"]:
                        game["scores"][user_id] = {"name": user_name, "score": 0}
                    game["scores"][user_id]["score"] += 1
                    game["scores"][user_id]["name"] = user_name
                else:
                    if user_id not in game["wrong"]:
                        game["wrong"][user_id] = {"name": user_name, "wrong": 0}
                    game["wrong"][user_id]["wrong"] += 1

async def end_quiz(chat_id):
    game = GROUP_GAMES.get(chat_id)
    if not game:
        return
    
    game["active"] = False
    scores = game.get("scores", {})
    wrong = game.get("wrong", {})
    
    total_players = len(set(list(scores.keys()) + list(wrong.keys())))
    total_correct = sum([s["score"] for s in scores.values()])
    total_wrong = sum([w["wrong"] for w in wrong.values()])
    
    if not scores and not wrong:
        await bot.send_message(
            chat_id,
            f"🌸💖✨ **MAHAKAL QUIZ** ✨💖🌸\n"
            f"╔════════════════════════════════╗\n"
            f"║        🏁 QUIZ OVER! 🏁       ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"😔 **Kisi ne answer nahi kiya!**\n\n"
            f"📝 **Type /quiz on to play again!**"
        )
        return
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    top_3 = sorted_scores[:3]
    
    leaderboard = (
        f"🌸💖✨ **MAHAKAL QUIZ** ✨💖🌸\n"
        f"╔════════════════════════════════════╗\n"
        f"║         🏆 WINNERS 🏆             ║\n"
        f"╚════════════════════════════════════╝\n\n"
    )
    
    medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    
    for i, (user_id, data) in enumerate(top_3):
        medal = medals[i] if i < 3 else f"{i+1}th"
        leaderboard += f"{medal} → **{data['name']}** - {data['score']} ✅\n"
    
    leaderboard += f"\n📊 **Total Players:** {len(scores)}\n"
    leaderboard += f"✅ **Total Correct Answers:** {total_correct}\n"
    leaderboard += f"❌ **Total Wrong Answers:** {total_wrong}\n"
    leaderboard += f"\n🌸💖 **Shukriya! Dobara Khelo!** 💖🌸"
    
    await bot.send_message(chat_id, leaderboard, parse_mode="Markdown")
    await bot.send_message(
        chat_id,
        f"🎉 **Type /quiz on to play again!** 🎉"
    )

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id].get("active"):
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("⏹️ **Quiz Stopped!** Type /quiz on to start again.")
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
        print("✅ Webhook set")
    else:
        print("⚠️ No webhook URL, using polling")
        await dp.start_polling(bot)
        return
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()
    print(f"🚀 MAHAKAL QUIZ Bot running on port {os.getenv('PORT', 10000)}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
