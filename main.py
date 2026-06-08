import asyncio
import os
import random
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Render se token uthayega
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Quiz State Management
class QuizStates(StatesGroup):
    playing = State()

# --- QUESTIONS DATABASE ---
# Tum isme aur bhi sawaal baad mein aaram se add kar sakte ho
QUESTIONS = {
    "Science": [
        {"q": "Pani ka chemical formula kya hai?", "options": ["H2O", "CO2", "O2", "NaCl"], "correct": "H2O"},
        {"q": "Humari body me total kitni bones (haddiyan) hoti hain?", "options": ["206", "306", "106", "506"], "correct": "206"}
    ],
    "Movies": [
        {"q": "Sholay movie me 'Gabbar Singh' ka role kisne kiya tha?", "options": ["Amjad Khan", "Amitabh Bachchan", "Dharmendra", "Sanjeev Kumar"], "correct": "Amjad Khan"},
        {"q": "Famous movie 'Bahubali' ke director kaun hain?", "options": ["S. S. Rajamouli", "Karan Johar", "Anurag Kashyap", "Sanjay Leela Bhansali"], "correct": "S. S. Rajamouli"}
    ],
    "GK": [
        {"q": "India ki capital (rajdhani) kya hai?", "options": ["New Delhi", "Mumbai", "Kolkata", "Chennai"], "correct": "New Delhi"},
        {"q": "Ek saal me total kitne din hote hain?", "options": ["365", "360", "355", "370"], "correct": "365"}
    ],
    "Tech": [
        {"q": "Python kya hai?", "options": ["Programming Language", "Web Browser", "Operating System", "Antivirus"], "correct": "Programming Language"},
        {"q": "iPhone kis company ka product hai?", "options": ["Apple", "Samsung", "Google", "Realme"], "correct": "Apple"}
    ]
}

# --- START COMMAND HANDLER ---
@router.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext):
    await state.clear() # Purana state clear karne ke liye
    
    name = message.from_user.first_name
    if not name:
        name = "User"
        
    upper_name = name[:10].upper()
    normal_name = name[:10]

    # Tumhara customized box layout
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
        "│    ▶ START QUIZ BELOW   │\n"
        "├─────────────────────────┤\n"
        "│ 🏆 1. Alex   │ 2. CHAND │\n"
        "├─────────────────────────┤\n"
        "│       © Chand           │\n"
        "└─────────────────────────┘"
    )
    
    # Clickable Buttons categories ke liye
    kb_builder = [
        [
            InlineKeyboardButton(text="📚 Science", callback_data="cat_Science"),
            InlineKeyboardButton(text="🎬 Movies", callback_data="cat_Movies")
        ],
        [
            InlineKeyboardButton(text="💡 GK", callback_data="cat_GK"),
            InlineKeyboardButton(text="💻 Tech", callback_data="cat_Tech")
        ]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_builder)
    
    # Telegram me design barabar dikhane ke liye <pre> lagaya hai
    await message.answer(
        f"<pre>{welcome_text}</pre>\n\n<b>Niche diye gaye button se Category select karo aur quiz shuru karo! 👇</b>", 
        parse_mode="HTML", 
        reply_markup=keyboard
    )

# --- CATEGORY SELECTION HANDLER ---
@router.callback_query(F.data.startswith("cat_"))
async def start_quiz_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    
    if category not in QUESTIONS:
        await callback.answer(f"Bhai, {category} ke questions jaldi add honge! Abhi Science, Movies, GK ya Tech chuno.", show_alert=True)
        return
        
    questions_list = QUESTIONS[category]
    q_index = 0
    q_data = questions_list[q_index]
    
    # State data save karna game track karne ke liye
    await state.set_state(QuizStates.playing)
    await state.update_data(category=category, q_index=q_index, score=0, correct_ans=q_data["correct"])
    
    # Options ke buttons banana
    options_kb = []
    for opt in q_data["options"]:
        options_kb.append([InlineKeyboardButton(text=opt, callback_data=f"ans_{opt}")])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=options_kb)
    
    await callback.message.edit_text(
        f"<b>📂 Category: {category}</b>\n\n<b>Sawaal 1:</b> {q_data['q']}", 
        parse_mode="HTML", 
        reply_markup=keyboard
    )
    await callback.answer()

# --- ANSWER CHECKER HANDLER ---
@router.callback_query(QuizStates.playing, F.data.startswith("ans_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    user_ans = callback.data.split("_")[1]
    data = await state.get_data()
    
    category = data["category"]
    q_index = data["q_index"]
    score = data["score"]
    correct_ans = data["correct_ans"]
    
    # Answer sahi hai ya galat check karna
    if user_ans == correct_ans:
        score += 1
        feedback = "✅ <b>Sahi Jawab! Shabaash!</b>"
    else:
        feedback = f"❌ <b>Galat Jawab!</b>\nSahi jawab tha: <code>{correct_ans}</code>"
        
    q_index += 1
    questions_list = QUESTIONS[category]
    
    # Agar aur sawaal bache hain
    if q_index < len(questions_list):
        next_q = questions_list[q_index]
        await state.update_data(q_index=q_index, score=score, correct_ans=next_q["correct"])
        
        options_kb = []
        for opt in next_q["options"]:
            options_kb.append([InlineKeyboardButton(text=opt, callback_data=f"ans_{opt}")])
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=options_kb)
        
        await callback.message.edit_text(
            f"{feedback}\n\n────────────────────\n\n<b>📂 Category: {category}</b>\n\n<b>Sawaal {q_index+1}:</b> {next_q['q']}", 
            parse_mode="HTML", 
            reply_markup=keyboard
        )
    else:
        # Agar saare sawaal khatam ho gaye
        await callback.message.edit_text(
            f"{feedback}\n\n🏁 <b>QUIZ KHATAM!</b>\n\n🏆 Tumhara Final Score: <b>{score}/{len(questions_list)}</b>\n\nDubara khelne ke liye /start dabayein.",
            parse_mode="HTML"
        )
        await state.clear() # Game khatam, state saaf
        
    await callback.answer()

# Router ko main dispatcher me jodna
dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
