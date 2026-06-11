import os
import asyncio
import random
import re
import json
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
        f"📊 *Bot Statistics*\n\n👥 Users: {len(users)}\n👥 Groups: {len(groups)}\n🤖 Status: Active",
        parse_mode="Markdown"
    )

@dp.message(Command("groups"))
async def show_groups(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only admin can see this!")
        return
    groups = load_groups()
    if not groups:
        await message.answer("No groups found.")
        return
    result = f"📊 *Groups ({len(groups)}):*\n\n"
    for gid, data in groups.items():
        result += f"• {data['name']}\n🆔 `{gid}`\n\n"
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
    for uid, data in list(users.items())[-20:]:
        result += f"• {data['name']} (@{data['username']})\n🆔 `{uid}`\n\n"
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Only admin can use this!")
        return
    msg = message.text.replace("/broadcast", "").strip()
    if not msg:
        await message.answer("Usage: /broadcast <message>")
        return
    status = await message.answer("📢 Broadcasting...")
    success, fail = await broadcast_message(msg)
    await status.edit_text(f"✅ Sent to {success} users\n❌ Failed: {fail}")

@dp.message(Command("sp"))
async def change_quiz_speed(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /sp <seconds>")
        return
    num = re.search(r'\d+', args[1])
    if num:
        if message.chat.id not in GROUP_GAMES:
            GROUP_GAMES[message.chat.id] = {"active": False, "speed": 15}
        GROUP_GAMES[message.chat.id]["speed"] = int(num.group())
        await message.answer(f"⚡ Speed: {num.group()}s")

@dp.message(lambda m: m.text and m.text.lower() in ['/quiz/on', '/quiz on'])
async def start_quiz(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    save_user(user_id, "", message.from_user.first_name or "")
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ Quiz already running!")
        return
    GROUP_GAMES[chat_id] = {
        "active": True,
        "speed": GROUP_GAMES[chat_id].get("speed", 15),
        "scores": {},
        "current_question": 0,
        "total_questions": 25,
        "questions": get_random_questions(25)
    }
    await message.answer(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✨ MAHAKAL QUIZ ✨\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📚 Questions: 25\n⏱️ Time: {GROUP_GAMES[chat_id]['speed']}s\n\n🔥 Best of Luck!")
    await send_question(chat_id)

async def send_question(chat_id):
    game = GROUP_GAMES.get(chat_id)
    if not game or not game["active"]:
        return
    idx = game["current_question"]
    if idx >= len(game["questions"]):
        await end_quiz(chat_id)
        return
    q = game["questions"][idx]
    text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✨ MAHAKAL QUIZ ✨\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📌 Q{idx+1}/{game['total_questions']}\n{q['q']}\n\n⏱️ Time: {game['speed']}s"
    poll = await bot.send_poll(chat_id, text, q['o'], type="quiz", correct_option_id=int(q['a']), open_period=game["speed"])
    game["current_poll_id"] = poll.poll.id
    game["current_question_data"] = q
    await asyncio.sleep(game["speed"] + 2)
    game["current_question"] += 1
    await send_question(chat_id)

@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    for chat_id, game in GROUP_GAMES.items():
        if game.get("current_poll_id") == poll_answer.poll_id:
            user_id = poll_answer.user.id
            user_name = poll_answer.user.first_name or "Unknown"
            q = game.get("current_question_data")
            if q:
                is_correct = (poll_answer.option_ids[0] == int(q['a'])) if poll_answer.option_ids else False
                if is_correct:
                    if user_id not in game["scores"]:
                        game["scores"][user_id] = {"name": user_name, "score": 0}
                    game["scores"][user_id]["score"] += 1

async def end_quiz(chat_id):
    game = GROUP_GAMES.get(chat_id)
    if not game:
        return
    game["active"] = False
    scores = game.get("scores", {})
    if not scores:
        await bot.send_message(chat_id, "😔 No one participated!")
        return
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    result = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏆 MAHAKAL QUIZ 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, data) in enumerate(sorted_scores[:3]):
        result += f"{medals[i] if i<3 else '📌'} {data['name']} → {data['score']} ✅\n"
    result += f"\n📊 Total Players: {len(scores)}\n/quiz on to play again!"
    await bot.send_message(chat_id, result)

@dp.message(lambda m: m.text and m.text.lower() in ['/quiz/off', '/quiz off'])
async def stop_quiz(message: types.Message):
    if message.chat.id in GROUP_GAMES:
        GROUP_GAMES[message.chat.id]["active"] = False
        await message.answer("⏹️ Quiz Stopped!")

async def handle_webhook(request):
    data = await request.json()
    await dp.feed_update(bot, types.Update(**data))
    return web.Response(text="OK")

async def main():
    port = int(os.getenv("PORT", 10000))
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    if RENDER_URL:
        await bot.set_webhook(url=f"{RENDER_URL}/webhook")
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"🚀 Bot running on port {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
