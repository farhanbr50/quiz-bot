import os
import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Files import
from welcome import get_welcome_text
from questions import QUESTIONS

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
            GROUP_GAMES[message.chat.id] = {"active": False, "speed": 15, "scores": {}}
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed set to {num.group()} seconds per question!")
    else:
        await message.answer("❌ Invalid number! Example: /sp 15")

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/on', '/quiz on'])
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15, "scores": {}}
    
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ Quiz already running! Use /quiz off to stop.")
        return
    
    if not QUESTIONS:
        await message.answer("❌ No questions available! Please contact admin.")
        return
    
    # Reset scores for new quiz
    GROUP_GAMES[chat_id] = {
        "active": True,
        "speed": GROUP_GAMES[chat_id].get("speed", 15),
        "scores": {},
        "current_question": 0,
        "total_questions": min(15, len(QUESTIONS))
    }
    
    # Take random questions
    selected_questions = random.sample(QUESTIONS, GROUP_GAMES[chat_id]["total_questions"])
    GROUP_GAMES[chat_id]["questions"] = selected_questions
    
    # MAHAKAL QUIZ HEADER
    await message.answer(
        f"🕉️═══════════════════════🕉️\n"
        f"     🔱 MAHAKAL QUIZ 🔱\n"
        f"🕉️═══════════════════════🕉️\n\n"
        f"📚 Total Questions: {GROUP_GAMES[chat_id]['total_questions']}\n"
        f"⏱️ Time per Question: {GROUP_GAMES[chat_id]['speed']} seconds\n\n"
        f"🔥 Har Har Mahadev! Let's Begin! 🔥"
    )
    
    # Send first question
    await send_question(chat_id)

async def send_question(chat_id):
    """Send current question to group"""
    game = GROUP_GAMES.get(chat_id)
    if not game or not game["active"]:
        return
    
    idx = game["current_question"]
    questions = game["questions"]
    
    if idx >= len(questions):
        await end_quiz(chat_id)
        return
    
    q = questions[idx]
    
    # Question with Mahakal name
    question_text = (
        f"🕉️ **MAHAKAL QUIZ** 🕉️\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"**Question {idx+1}/{game['total_questions']}**\n\n"
        f"{q['q']}\n\n"
        f"⏱️ Time: {game['speed']} seconds"
    )
    
    # Store poll message ID to track answers
    poll_message = await bot.send_poll(
        chat_id,
        question_text,
        q['o'],
        type="quiz",
        correct_option_id=int(q['a']),
        open_period=game["speed"]
    )
    
    # Store poll info to track who answered
    game["current_poll_id"] = poll_message.poll.id
    game["current_question_data"] = q
    
    # Wait for question time
    await asyncio.sleep(game["speed"] + 1)
    
    # Move to next question
    game["current_question"] += 1
    await send_question(chat_id)

@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    """Track each user's score"""
    for chat_id, game in GROUP_GAMES.items():
        if not game.get("active"):
            continue
        
        # Check if this poll is from current question
        if game.get("current_poll_id") == poll_answer.poll_id:
            user_id = poll_answer.user.id
            user_name = poll_answer.user.first_name or "Unknown"
            
            # Check if answer is correct (option_id 0 = first option)
            # For quiz poll, correct_option_id is stored in question data
            current_q = game.get("current_question_data")
            if current_q:
                correct_answer = int(current_q['a'])
                user_answer = poll_answer.option_ids[0] if poll_answer.option_ids else -1
                
                if user_answer == correct_answer:
                    # Increment score
                    if user_id not in game["scores"]:
                        game["scores"][user_id] = {"name": user_name, "score": 0}
                    game["scores"][user_id]["score"] += 1
                    game["scores"][user_id]["name"] = user_name

async def end_quiz(chat_id):
    """End quiz and show winners"""
    game = GROUP_GAMES.get(chat_id)
    if not game:
        return
    
    game["active"] = False
    
    # Get top 3 winners
    scores = game.get("scores", {})
    
    if not scores:
        await bot.send_message(
            chat_id,
            f"🕉️═══════════════════════🕉️\n"
            f"     🏁 QUIZ COMPLETED! 🏁\n"
            f"🕉️═══════════════════════🕉️\n\n"
            f"😔 Kisi ne answer nahi kiya!\n\n"
            f"🔱 Har Har Mahadev! 🔱"
        )
        return
    
    # Sort by score (highest first)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    top_3 = sorted_scores[:3]
    
    # Prepare leaderboard message
    leaderboard = f"🕉️═══════════════════════🕉️\n"
    leaderboard += f"     🏆 WINNERS 🏆\n"
    leaderboard += f"🕉️═══════════════════════🕉️\n\n"
    
    # Medal emojis
    medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    
    for i, (user_id, data) in enumerate(top_3):
        medal = medals[i] if i < 3 else f"{i+1}th"
        leaderboard += f"{medal} → **{data['name']}** - {data['score']} ✅\n"
    
    leaderboard += f"\n📊 Total Players: {len(scores)}\n"
    leaderboard += f"\n🔱 Har Har Mahadev! 🔱"
    
    # Also show full scores (optional)
    full_scores = "\n📋 **Full Scores:**\n"
    for user_id, data in sorted_scores[:10]:  # Top 10
        full_scores += f"   • {data['name']}: {data['score']} ✅\n"
    
    await bot.send_message(chat_id, leaderboard)
    if len(sorted_scores) > 3:
        await bot.send_message(chat_id, full_scores)
    
    await bot.send_message(
        chat_id,
        f"🙏 Thanks for playing Mahakal Quiz!\n"
        f"Type /quiz on to play again! 🔱"
    )

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id].get("active"):
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer(
            f"🕉️ **MAHAKAL QUIZ STOPPED** 🕉️\n"
            f"Quiz rok di gayi. /quiz on se dobara start karein!"
        )
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
        print("⚠️ No webhook URL set, using polling mode (for local testing)")
        await dp.start_polling(bot)
        return
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()
    print(f"🚀 Mahakal Quiz Bot running on port {os.getenv('PORT', 10000)}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
