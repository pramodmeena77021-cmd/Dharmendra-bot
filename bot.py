import os
from collections import deque
from google import genai
from google.genai import types
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==========================================
# 1. API KEYS & TOKENS (Apni nayi keys yahan daalein)
# ==========================================
API_KEY = os.environ.get("API_KEY", "APNI_NAYI_GEMINI_API_KEY_YAHAN_DAALEIN")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "APNA_NAYA_BOT_TOKEN_YAHAN_DAALEIN")

# Initialize Google Gemini Client
client = genai.Client(api_key=API_KEY)

# ==========================================
# 2. MEMORY & LANGUAGE STORAGE
# ==========================================
user_languages = {}
chat_history = {}

def get_system_prompt(lang: str) -> str:
    language_rules = {
        "hinglish": "Talk in natural, everyday Hinglish (a mix of Hindi written in Roman script and simple English words). Use friendly expressions like 'Arre bhai', 'Sun yaar', 'Tension mat le', 'Chill kar'.",
        "hindi": "शुद्ध और सरल हिंदी (Devanagari script) में बात करो। दोस्तों जैसा अपनापन रखो जैसे 'अरे भाई', 'सुन यार', 'चिंता मत कर'। भारी किताबी शब्दों से बचो।",
        "english": "Talk in casual, friendly, everyday English like a supportive senior student or mentor. Use natural phrases like 'Hey bro', 'Don't stress', 'Let's break this down'."
    }
    
    selected_lang_rule = language_rules.get(lang, language_rules["hinglish"])
    
    return f"""
You are a smart, caring, and chill senior friend (mentor/older brother) who helps NEET & science students with their studies and life.

Your personality and rules:
1. **Language Style:** {selected_lang_rule} Never sound like a robotic textbook or strict teacher.
2. **Studies & NCERT Doubts:** When asked about Physics, Chemistry, Biology, or any subject, explain concepts using simple real-life examples and NCERT logic so they stick in the student's head immediately.
3. **Motivation & Emotional Support:** If a student feels low, stressed about exams, or overwhelmed by personal issues, listen without judging, comfort them first, and then give practical life advice and solid motivation.
4. **Humor:** Keep the vibe light with occasional friendly jokes and banter, while staying mature during serious moments.
5. **Formatting:** Keep replies concise, punchy, and easy to read on a phone screen using bullet points where needed.
"""

# ==========================================
# 3. BOT COMMANDS & HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_languages.setdefault(user_id, "hinglish")
    chat_history[user_id] = deque(maxlen=6)
    
    welcome_msg = (
        f"Hey {user_name}! Kya haal hai bhai? 😎\n\n"
        "Studies ka koi doubt ho (Physics, Chem, Bio), exam stress ho, ya bas baat karni ho — I'm right here with you.\n\n"
        "• /settings — Language change karne ke liye (Hinglish / Hindi / English)\n"
        "• /clear — Purani chat memory reset karne ke liye"
    )
    await update.message.reply_text(welcome_msg)

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_history[user_id] = deque(maxlen=6)
    await update.message.reply_text("Memory clear kar di bhai! Ab fresh start karte hain. 🚀")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Hinglish (Default)", callback_data="lang_hinglish"),
            InlineKeyboardButton("अ हिंदी (Hindi)", callback_data="lang_hindi"),
        ],
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your preferred language / अपनी भाषा चुनें:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    choice = query.data.replace("lang_", "")
    user_languages[user_id] = choice
    
    confirmations = {
        "hinglish": "Done bhai! Ab hum Hinglish mein baat karenge. 😎",
        "hindi": "बढ़िया! अब से हम हिंदी में बात करेंगे। 😊",
        "english": "Got it! We'll chat in English from now on. 👍"
    }
    await query.edit_message_text(text=confirmations.get(choice, "Language updated!"))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_type = update.effective_chat.type
    user_text = update.message.text
    bot_username = context.bot.username

    if chat_type in ["group", "supergroup"]:
        is_mentioned = f"@{bot_username}" in user_text if bot_username else False
        is_reply_to_bot = (
            update.message.reply_to_message 
            and update.message.reply_to_message.from_user.id == context.bot.id
        )
        if not (is_mentioned or is_reply_to_bot):
            return
        if bot_username:
            user_text = user_text.replace(f"@{bot_username}", "").strip()

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    current_lang = user_languages.get(user_id, "hinglish")
    
    if user_id not in chat_history:
        chat_history[user_id] = deque(maxlen=6)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    past_context = "\n".join(chat_history[user_id])
    full_prompt = f"Student Name: {user_name}\nRecent Chat:\n{past_context}\n\nCurrent Message: {user_text}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt(current_lang),
                temperature=0.8,
            )
        )
        reply_text = response.text
        
        chat_history[user_id].append(f"Student: {user_text}")
        chat_history[user_id].append(f"Mentor: {reply_text}")
        
        await update.message.reply_text(reply_text)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Network glitch aa gaya yaar 😅, ek second baad dobara try kar!")

# ==========================================
# 4. START APPLICATION
# ==========================================
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('settings', settings))
    app.add_handler(CommandHandler('clear', clear_memory))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("NEET Mentor Bot is running...")
    app.run_polling(drop_pending_updates=True)
