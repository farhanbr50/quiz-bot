import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

# Render se token uthayega
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def send_welcome(message: Message):
    # User ka naam nikalna
    name = message.from_user.first_name
    if not name:
        name = "User"
    
    upper_name = name[:10].upper()
    normal_name = name[:10]

    # Tumhara custom box design (User ka naam automatically set hoga)
    welcome_text = (
        "┌─────────────────────────┐\n"
        "│       QUIZ BOT          │\n"
        f"│    Welcome, {upper_name}! 👋   │\n"
        "├─────────────────────────┤\n"
        f"│ Hello {normal_name}! I'm your   │\n"
        "│ intelligent quiz bot    │\n"
        "├─────────────────────────┤\n"
        "│ 🔥12 │ ⭐2840 │ 🏆#42 │\n"
        "├─────────────────────────┤\n"
        "│ 📚 Science    🎬 Movies  │\n"
        "│ 📜 History    🎵 Music   │\n"
        "│ 🌍 Geography  📖 Lit.    │\n"
        "│ ⚽ Sports     🎨 Art     │\n"
        "│ 💻 Tech       🐾 Animals │\n"
        "│ 🚀 Space      💡 GK      │\n"
        "├─────────────────────────┤\n"
        "│    ▶ /start_quiz        │\n"
        "├─────────────────────────┤\n"
        "│ 🏆 1. Alex   │ 2. CHAND │\n"
        "├─────────────────────────┤\n"
        "│       © Chand           │\n"
        "└─────────────────────────┘"
    )
    
    # <pre> tag lagana zaroori hai warna Telegram me ye design aage-piche ho jayega
    await message.answer(f"<pre>{welcome_text}</pre>", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(m
                ain())
