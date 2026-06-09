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
        await message.answer("❌ Usage: /sp <seconds>")
        return
    num = re.search(r'\d+', args[1])
    if num:
        if message.chat.id not in GROUP_GAMES:
            GROUP_GAMES[message.chat.id] = {"active": False, "speed": 15, "scores": {}, "question_results": {}}
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed: {num.group()} seconds")

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/on', '/quiz on'])
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15, "scores": {}, "question_results": {}}
    
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ Quiz already running!")
        return
    
    GROUP_GAMES[chat_id] = {
        "active": True,
        "speed": GROUP_GAMES[chat_id].get("speed", 15),
        "scores": {},
        "question_results": {},
        "current_question": 0,
        "total_questions": 25
    }
    
    GROUP_GAMES[chat_id]["questions"] = get_random_questions(25)
    
    await message.answer(
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"        ✨ MAHAKAL QUIZ ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 Questions: {GROUP_GAMES[chat_id]['total_questions']}\n"
        f"⏱️ Time: {GROUP_GAMES[chat_id]['speed']} seconds\n\n"
        f"🔥 Best of Luck! 🔥"
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
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"        ✨ MAHAKAL QUIZ ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 Q{idx+1}/{game['total_questions']}\n"
        f"{q['q']}\n\n"
        f"⏱️ Time: {game['speed']} seconds"
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
    game["current_question_num"] = idx + 1
    game["question_results"][idx] = {"q": q['q'], "correct": q['a'], "answers": {}, "options": q['o']}
    
    await asyncio.sleep(game["speed"] + 2)
    
    # After question ends, send results to group
    await send_question_results(chat_id, idx)
    
    game["current_question"] += 1
    await send_question(chat_id)

async def send_question_results(chat_id, question_idx):
    game = GROUP_GAMES.get(chat_id)
    if not game:
        return
    
    q_data = game["question_results"].get(question_idx, {})
    if not q_data:
        return
    
    answers = q_data.get("answers", {})
    correct_option = int(q_data.get("correct", 0))
    options = q_data.get("options", [])
    question_text = q_data.get("q", "")
    
    if not answers:
        await bot.send_message(
            chat_id,
            f"📊 Question {question_idx + 1} Results:\n"
            f"❌ No one answered this question!"
        )
        return
    
    # Group by correct and wrong
    correct_users = []
    wrong_users = []
    
    for user_id, data in answers.items():
        if data["is_correct"]:
            correct_users.append(f"✅ {data['name']}")
        else:
            wrong_users.append(f"❌ {data['name']} → {data['answer_text']}")
    
    result_text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Question {question_idx + 1} Results\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 {question_text}\n"
        f"✓ Correct Answer: {options[correct_option]}\n\n"
    )
    
    if correct_users:
        result_text += f"🎉 Correct Answers ({len(correct_users)}):\n"
        for user in correct_users:
            result_text += f"{user}\n"
        result_text += f"\n"
    
    if wrong_users:
        result_text += f"❌ Wrong Answers ({len(wrong_users)}):\n"
        for user in wrong_users[:10]:  # Max 10 wrong answers show
            result_text += f"{user}\n"
        if len(wrong_users) > 10:
            result_text += f"... and {len(wrong_users) - 10} more\n"
    
    await bot.send_message(chat_id, result_text)

@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    for chat_id, game in GROUP_GAMES.items():
        if not game.get("active"):
            continue
        
        if game.get("current_poll_id") == poll_answer.poll_id:
            user_id = poll_answer.user.id
            user_name = poll_answer.user.first_name or "Unknown"
            
            current_q = game.get("current_question_data")
            current_idx = game.get("current_question_num", 0) - 1
            
            if current_q and current_idx >= 0:
                correct_answer = int(current_q['a'])
                user_answer = poll_answer.option_ids[0] if poll_answer.option_ids else -1
                
                is_correct = (user_answer == correct_answer)
                answer_text = current_q['o'][user_answer] if user_answer != -1 else "No answer"
                
                # Store answer in question_results
                if current_idx not in game["question_results"]:
                    game["question_results"][current_idx] = {"answers": {}}
                
                game["question_results"][current_idx]["answers"][user_id] = {
                    "name": user_name,
                    "answer": user_answer,
                    "answer_text": answer_text,
                    "is_correct": is_correct
                }
                
                # Update score
                if is_correct:
                    if user_id not in game["scores"]:
                        game["scores"][user_id] = {"name": user_name, "score": 0}
                    game["scores"][user_id]["score"] += 1
                    game["scores"][user_id]["name"] = user_name

async def end_quiz(chat_id):
    game = GROUP_GAMES.get(chat_id)
    if not game:
        return
    
    game["active"] = False
    scores = game.get("scores", {})
    
    if not scores:
        await bot.send_message(
            chat_id,
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"        🏁 QUIZ OVER! 🏁\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"😔 No one participated!\n\n"
            f"📝 /quiz on to play again!"
        )
        return
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    result = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"        🏆 MAHAKAL QUIZ 🏆\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏅 FINAL WINNERS 🏅\n\n"
    )
    
    medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    for i, (user_id, data) in enumerate(sorted_scores[:3]):
        medal = medals[i] if i < 3 else f"{i+1}th"
        result += f"{medal} → {data['name']} → {data['score']} ✅\n"
    
    result += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    result += f"📊 Total Players: {len(scores)}\n"
    
    total_correct = sum([s["score"] for s in scores.values()])
    result += f"🎯 Total Correct: {total_correct}\n"
    result += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🌸 Thanks for playing! 🌸\n"
    result += f"/quiz on to play again!"
    
    await bot.send_message(chat_id, result)
    
    # Full scoreboard
    if len(sorted_scores) > 3:
        full = f"📋 Complete Scoreboard:\n\n"
        for i, (user_id, data) in enumerate(sorted_scores[:10]):
            full += f"{i+1}. {data['name']} → {data['score']} ✅\n"
        await bot.send_message(chat_id, full)

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id].get("active"):
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("⏹️ Quiz Stopped! /quiz on to start again.")
    else:
        await message.answer("❌ No active quiz!")

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
        print("⚠️ Polling mode")
        await dp.start_polling(bot)
        return
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()
    print(f"🚀 MAHAKAL QUIZ Bot running")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
