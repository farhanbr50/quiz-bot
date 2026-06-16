import os
import asyncio
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")

# Global Variables
quiz_status = {}
quiz_speed = {}

# Quiz Data - Sab Hindi (Romanized) mein
QUESTIONS = [
    {
        "q": "Farhan Mod II ka favourite drama kaunsa hai?",
        "options": ["The Blue Whisper", "Legend of the Blue Sea", "Dono", "Koi nahi"],
        "correct": 2
    },
    {
        "q": "Darbhanga ka sabse famous khana kya hai?",
        "options": ["Litti Chokha", "Biryani", "Pizza", "Samosa"],
        "correct": 0
    },
    {
        "q": "Telegram par music bot chalane ke liye kaunsa language best hai?",
        "options": ["Java", "Python", "C++", "PHP"],
        "correct": 1
    }
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == 'private':
        welcome_text = (
            "✨ **Welcome to Farhan Quiz Bot!** ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👋 Hello! I am your personal Quiz Bot.\n"
            "🎮 Add me to your group to start the fun.\n"
            "⚙️ Commands: /quiz@on, /quiz@off, /speed@10\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 *Design by Farhan Mod II*"
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def toggle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cmd = update.message.text
    
    if "on" in cmd:
        quiz_status[chat_id] = True
        await update.message.reply_text("✅ **Quiz Mode: ACTIVATED**")
        asyncio.create_task(quiz_loop(chat_id, context))
    else:
        quiz_status[chat_id] = False
        await update.message.reply_text("❌ **Quiz Mode: DEACTIVATED**")

async def set_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text
    speed_val = cmd.split("@")[1]
    seconds = int(speed_val.replace('m', '')) * 60 if 'm' in speed_val else int(speed_val)
    quiz_speed[update.effective_chat.id] = seconds
    await update.message.reply_text(f"⏱ **Speed set to: {speed_val}**")

async def quiz_loop(chat_id, context):
    while quiz_status.get(chat_id):
        q_data = random.choice(QUESTIONS)
        await context.bot.send_poll(
            chat_id=chat_id,
            question=q_data["q"],
            options=q_data["options"],
            type='quiz',
            correct_option_id=q_data["correct"],
            is_anonymous=False,
            explanation="Ye raha sahi jawab! ✨"
        )
        await asyncio.sleep(quiz_speed.get(chat_id, 10))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz@on", toggle_quiz))
    app.add_handler(CommandHandler("quiz@off", toggle_quiz))
    # Handlers for speeds
    for s in ["5", "10", "15", "20", "1m", "2m"]:
        app.add_handler(CommandHandler(f"speed@{s}", set_speed))
    
    app.run_po
  lling()
