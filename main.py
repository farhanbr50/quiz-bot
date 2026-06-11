import os
import asyncio
import random
import re
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated
from aiohttp import web

from welcome import get_welcome_text
from questions import get_random_questions

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

GROUP_GAMES = {}

# Files to store data
USERS_FILE = "users.json"
GROUPS_FILE = "groups.json"

# Admin IDs - YOUR TELEGRAM ID
ADMINS = [560588833]

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_user(user_id, username, first_name):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "name": first_name,
            "first_seen": str(asyncio.get_event_loop().time())
        }
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
        return True
    return False

def load_groups():
    try:
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_group(group_id, group_name):
    groups = load_groups()
    if str(group_id) not in groups:
        groups[str(group_id)] = {
            "name": group_name,
            "added_at": str(asyncio.get_event_loop().time())
        }
        with open(GROUPS_FILE, "w") as f:
            json.dump(groups, f, indent=2)
        return True
    return False

def remove_group(group_id):
    groups = load_groups()
    if str(group_id) in groups:
        del groups[str(group_id)]
        with open(GROUPS_FILE, "w") as f:
            json.dump(groups, f, indent=2)
        return True
    return False

async def broadcast_message(message_text):
    users = load_users()
    success_count = 0
    fail_count = 0
    
    for user_id, data in users.items():
        try:
            await bot.send_message(int(user_id), message_text)
            success_count += 1
            await asyncio.sleep(0.05)
        except:
            fail_count += 1
    
    return success_count, fail_count

@dp.my_chat_member()
async def track_groups(update: ChatMemberUpdated):
    """Track when bot is added/removed from groups"""
    chat = update.chat
    if chat.type in ['group', 'supergroup']:
        if update.new_chat_member.status in ['member', 'administrator']:
            save_group(chat.id, chat.title)
            print(f"✅ Bot added to group: {chat.title}")
        elif update.new_chat_member.status == 'left':
            remove_group(chat.id)
            print(f"❌ Bot removed from group: {chat.title}")

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    first_name = message.from_user.first_name or "Unknown"
    
    is_new = save_user(user_id, username, first_name)
    user_name = first_name.upper()
    
    welcome_msg = get_welcome_text(user_name)
    
    users = load_users()
    if is_new:
        welcome_msg += f"\n\n✨ Aap humare {len(users)}ve user hain!"
    
    await message.answer(welcome_msg, parse_mode="Markdown")

@dp.message(Command("totalusers"))
async def show_total_users(message: types.Message):
    users = load_users()
    total = len(users)
    
    await message.answer(
        f"📊 *MAHAKAL QUIZ - User Statistics*\n\n"
        f"👥 *Total Users:* {total}\n"
        f"🤖 *Bot Status:* Active ✅\n\n"
        f"📝 *Commands:*\n"
        f"/quiz on - Start quiz\n"
        f"/broadcast - Send message to all\n"
        f"/groups - Show all groups",
        parse_mode="Markdown"
    )

@dp.message(Command("groups"))
async def show_groups(message: types.Message):
    """Show all groups where bot is added (Admin only)"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only bot admin can see this!")
        return
    
    groups = load_groups()
    total = len(groups)
    
    if total == 0:
        await message.answer("📊 No groups found! Bot is not added to any group yet.\n\nAdd bot to a group and make it admin to track.")
        return
    
    result = f"📊 *MAHAKAL QUIZ - Groups List*\n\n"
    result += f"👥 *Total Groups:* {total}\n\n"
    result += f"📋 *Group Details:*\n"
    
    for i, (group_id, data) in enumerate(groups.items()):
        result += f"{i+1}. *{data['name']}*\n"
        result += f"   🆔 ID: `{group_id}`\n\n"
    
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("userslist"))
async def show_users_list(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only bot admin can see this!")
        return
    
    users = load_users()
    total = len(users)
    
    user_list = f"📊 *Total Users:* {total}\n\n"
    user_list += "🆔 *All Users:*\n"
    
    for i, (uid, data) in enumerate(list(users.items())[-50:]):
        user_list += f"{i+1}. {data['name']} (@{data['username']}) - ID: `{uid}`\n"
    
    if len(users) > 50:
        user_list += f"\n... aur {len(users) - 50} users aur hain"
    
    await message.answer(user_list, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only bot admin can use this command!")
        return
    
    msg_text = message.text.replace("/broadcast", "").strip()
    
    if not msg_text:
        await message.answer(
            "📢 *Broadcast Command Usage:*\n\n"
            "/broadcast <message>\n\n"
            "Example:\n"
            "/broadcast Bot online hai! /quiz on se khelo!",
            parse_mode="Markdown"
        )
        return
    
    status_msg = await message.answer("📢 *Broadcast started...*", parse_mode="Markdown")
    
    success, fail = await broadcast_message(msg_text)
    
    await status_msg.edit_text(
        f"✅ *Broadcast Completed!*\n\n"
        f"📤 Sent to: {success} users\n"
        f"❌ Failed: {fail} users\n"
        f"📊 Total users: {success + fail}",
        parse_mode="Markdown"
    )

@dp.message(Command("stats"))
async def show_bot_stats(message: types.Message):
    users = load_users()
    groups = load_groups()
    total_users = len(users)
    total_groups = len(groups)
    
    await message.answer(
        f"📊 *MAHAKAL QUIZ - Bot Statistics*\n\n"
        f"👥 Total Users: {total_users}\n"
        f"👥 Total Groups: {total_groups}\n"
        f"🤖 Bot Status: Active ✅\n\n"
        f"Type /quiz on to start playing!",
        parse_mode="Markdown"
    )

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
    
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Unknown"
    save_user(user_id, username, first_name)
    
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
            f"📊 Question {question_idx + 1} Results:\n❌ No one answered!"
        )
        return
    
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
        f"✓ Correct: {options[correct_option]}\n\n"
    )
    
    if correct_users:
        result_text += f"🎉 Correct ({len(correct_users)}):\n" + "\n".join(correct_users) + "\n\n"
    
    if wrong_users:
        result_text += f"❌ Wrong ({len(wrong_users)}):\n" + "\n".join(wrong_users[:10])
        if len(wrong_users) > 10:
            result_text += f"\n... and {len(wrong_users) - 10} more"
    
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
                
                if current_idx not in game["question_results"]:
                    game["question_results"][current_idx] = {"answers": {}}
                
                game["question_results"][current_idx]["answers"][user_id] = {
                    "name": user_name,
                    "answer": user_answer,
                    "answer_text": answer_text,
                    "is_correct": is_correct
                }
                
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
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n😔 No one participated!"
        )
        return
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    result = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n        🏆 MAHAKAL QUIZ 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🏅 FINAL WINNERS 🏅\n\n"
    
    medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    for i, (user_id, data) in enumerate(sorted_scores[:3]):
        medal = medals[i] if i < 3 else f"{i+1}th"
        result += f"{medal} → {data['name']} → {data['score']} ✅\n"
    
    result += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 Total Players: {len(scores)}\n🎯 Total Correct: {sum([s['score'] for s in scores.values()])}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🌸 Thanks for playing!\n/quiz on to play again!"
    
    await bot.send_message(chat_id, result)

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id].get("active"):
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("⏹️ Quiz Stopped!")
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
