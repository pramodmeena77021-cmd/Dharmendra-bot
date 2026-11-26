import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from google import genai
from google.genai import types

# Load keys securely from Render Environment Variables
API_KEY = ("AQ.Ab8RN6Ls65bTNw2bJ2witfymeTJtHFR6V5Imep9Vx3gzi3Ejyw")
BOT_TOKEN = ("9172201952:AAFIg6621AcWo1PAB5kSxL7gSUno-SrV7Bk")

client = genai.Client(api_key=API_KEY)

# Store user language preferences (Default: Hinglish)
user_languages = {}

def get_system_prompt(lang: str) -> str:
    language_rules = {
        "hinglish": "Talk in natural, everyday Hinglish (a mix of Hindi written in Roman script and simple English words). Use friendly expressions like 'Arre bhai', 'Sun yaar', 'Tension mat le', 'Chill kar'.",
        "hindi": "शुद्ध और सरल हिंदी (Devanagari script) में बात करो। दोस्तों जैसा अपनापन रखो जैसे 'अरे भाई', 'सुन यार', 'चिंता मत कर'। भारी किताबी शब्दों से बचो।",
        "english": "Talk in casual, friendly, everyday English like a supportive senior student or mentor. Use natural phrases like 'Hey bro', 'Don't stress', 'Let's break this down'."
    }
    
    selected_lang_rule = language_rules.get(lang, language_rules["hinglish"])
    
    return f"""
You are a smart, caring, and chill senior friend (mentor/older brother) who helps students with their studies and life.

Your personality and rules:
1. **Language Style:** {selected_lang_rule} Never sound like a robotic textbook or strict teacher.
2. **Studies & Doubts:** When asked about Physics, Chemistry, Biology, or any subject, explain concepts using simple real-life examples so they stick in the student's head immediately.
3. **Motivation & Emotional Support:** If a student feels low, stressed about exams, or overwhelmed by personal issues, listen without judging, comfort them first, and then give practical life advice and solid motivation.
4. **Humor:** Keep the vibe light with occasional friendly jokes and banter, while staying mature during serious moments.
5. **Length:** Keep replies concise, punchy, and easy to read on a phone screen unless a detailed topic explanation is requested.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_languages.setdefault(user_id, "hinglish")
    
    welcome_msg = (
        f"Hey {user_name}! Kya haal hai bhai? 😎\n\n"
        "Studies ka koi doubt ho, exam stress ho, ya bas baat karni ho — I'm right here with you.\n"
        "Use /settings anytime to change my language (Hinglish / Hindi / English)."
    )
    await update.message.reply_text(welcome_msg)

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
    user_id = update.effective_user.id
    user_text = update.message.text
    current_lang = user_languages.get(user_id, "hinglish")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt(current_lang),
                temperature=0.8,
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Network glitch aa gaya yaar 😅, try again in a second!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('settings', settings))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()
