import os
import asyncio
import random
import re
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated

from welcome import get_welcome_text
from questions import get_random_questions

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

GROUP_GAMES = {}
USERS_FILE = "users.json"
GROUPS_FILE = "groups.json"
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

def remove_group(group_id):
    groups = load_groups()
    if str(group_id) in groups:
        del groups[str(group_id)]
        with open(GROUPS_FILE, "w") as f:
            json.dump(groups, f, indent=2)

async def broadcast_message(message_text):
    users = load_users()
    success = 0
    fail = 0
    for user_id in users:
        try:
            await bot.send_message(int(user_id), message_text)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1
    return success, fail

@dp.my_chat_member()
async def track_groups(update: ChatMemberUpdated):
    chat = update.chat
    if chat.type in ['group', 'supergroup']:
        if update.new_chat_member.status in ['member', 'administrator']:
            save_group(chat.id, chat.title)
            print(f"✅ Bot added to: {chat.title}")
        elif update.new_chat_member.status == 'left':
            remove_group(chat.id)
            print(f"❌ Bot removed from: {chat.title}")

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
    await message.answer(f"📊 *Total Users:* {len(users)}", parse_mode="Markdown")

@dp.message(Command("stats"))
async def show_bot_stats(message: types.Message):
    users = load_users()
    groups = load_groups()
    await message.answer(
        f"📊 *Bot Statistics*\n\n👥 Users: {len(users)}\n👥 Groups: {len(groups)}\n🤖 Status: Active ✅",
        parse_mode="Markdown"
    )

@dp.message(Command("groups"))
async def show_groups(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only admin can see this!")
        return
    groups = load_groups()
    if not groups:
        await message.answer("📊 No groups found!\n\nAdd bot to a group and make it admin.")
        return
    result = f"📊 *Groups ({len(groups)}):*\n\n"
    for gid, data in groups.items():
        result += f"📌 *{data['name']}*\n🆔 `{gid}`\n\n"
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("userslist"))
async def show_users_list(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only admin can see this!")
        return
    users = load_users()
    if not users:
        await message.answer("No users found.")
        return
    result = f"📊 *Users ({len(users)}):*\n\n"
    for i, (uid, data) in enumerate(list(users.items())[-30:]):
        result += f"{i+1}. {data['name']} (@{data['username']})\n🆔 `{uid}`\n\n"
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only admin can use this!")
        return
    msg = message.text.replace("/broadcast", "").strip()
    if not msg:
        await message.answer("Usage: /broadcast <message>\n\nExample:\n/broadcast Bot online hai!")
        return
    status = await message.answer("📢 Broadcasting...")
    success, fail = await broadcast_message(msg)
    await status.edit_text(f"✅ Broadcast Completed!\n\n📤 Sent to: {success} users\n❌ Failed: {fail}")

@dp.message(Command("sp"))
async def change_quiz_speed(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Usage: /sp <seconds>\nExample: /sp 15")
        return
    num = re.search(r'\d+', args[1])
    if num:
        if message.chat.id not in GROUP_GAMES:
            GROUP_GAMES[message.chat.id] = {"active": False, "speed": 15}
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed set to {num.group()} seconds!")
    else:
        await message.answer("❌ Invalid number! Example: /sp 15")

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/on', '/quiz on'])
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Unknown"
    save_user(user_id, username, first_name)
    
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
    
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ Quiz already running! Use /quiz off to stop.")
        return
    
    GROUP_GAMES[chat_id] = {
        "active": True,
        "speed": GROUP_GAMES[chat_id].get("speed", 15),
        "scores": {},
        "current_question": 0,
        "total_questions": 25,
        "questions": get_random_questions(25)
    }
    
    await message.answer(
        f"┌────────────────────────────────────────┐\n"
        f"│         ✨ 𝕄𝔸ℍ𝔸𝕂𝔸𝕃 ℚ𝕌𝕀ℤ ✨          │\n"
        f"├────────────────────────────────────────┤\n"
        f"│  📚 Questions  : {GROUP_GAMES[chat_id]['total_questions']:<2}                   │\n"
        f"│  ⏱️ Time       : {GROUP_GAMES[chat_id]['speed']:<2} seconds                │\n"
        f"├────────────────────────────────────────┤\n"
        f"│         🔥 Best of Luck! 🔥           │\n"
        f"└────────────────────────────────────────┘"
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
        f"┌────────────────────────────────────────┐\n"
        f"│         ✨ 𝕄𝔸ℍ𝔸𝕂𝔸𝕃 ℚ𝕌𝕀ℤ ✨          │\n"
        f"├────────────────────────────────────────┤\n"
        f"│  📌 Question {idx+1}/{game['total_questions']:<2}                      │\n"
        f"├────────────────────────────────────────┤\n"
        f"│  {q['q']:<38} │\n"
        f"├────────────────────────────────────────┤\n"
        f"│  ⏱️ Time : {game['speed']} seconds                     │\n"
        f"└────────────────────────────────────────┘"
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
    
    await asyncio.sleep(game["speed"] + 2)
    
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

async def end_quiz(chat_id):
    game = GROUP_GAMES.get(chat_id)
    if not game:
        return
    
    game["active"] = False
    scores = game.get("scores", {})
    
    if not scores:
        await bot.send_message(
            chat_id,
            f"┌────────────────────────────────────────┐\n"
            f"│           🏁 QUIZ OVER! 🏁            │\n"
            f"├────────────────────────────────────────┤\n"
            f"│         😔 No one participated!        │\n"
            f"└────────────────────────────────────────┘"
        )
        return
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    result = f"┌────────────────────────────────────────┐\n"
    result += f"│         🏆 𝕄𝔸ℍ𝔸𝕂𝔸𝕃 ℚ𝕌𝕀ℤ 🏆          │\n"
    result += f"├────────────────────────────────────────┤\n"
    
    medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    for i, (user_id, data) in enumerate(sorted_scores[:3]):
        medal = medals[i] if i < 3 else f"{i+1}th"
        result += f"│  {medal} → {data['name']:<10} → {data['score']:>2} ✅   │\n"
    
    result += f"├────────────────────────────────────────┤\n"
    result += f"│  📊 Total Players : {len(scores):>2}                   │\n"
    result += f"│  🎯 Total Correct : {sum([s['score'] for s in scores.values()]):>2}                   │\n"
    result += f"└────────────────────────────────────────┘\n\n"
    result += f"🌸 Thanks for playing!\n/quiz on to play again!"
    
    await bot.send_message(chat_id, result)

@dp.message(lambda message: message.text and message.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id].get("active"):
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("⏹️ Quiz Stopped! /quiz on to start again.")
    else:
        await message.answer("❌ No active quiz to stop!")

async def main():
    print("🚀 MAHAKAL QUIZ Bot starting in POLLING mode...")
    print("🤖 Bot is now live! Press Ctrl+C to stop.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
