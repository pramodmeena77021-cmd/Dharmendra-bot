import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai

# Gemini client setup (Make sure GEMINI_API_KEY is set in Render Environment Variables)
client = genai.Client()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your friendly NEET tutor. Ask me anything about Biology, Chemistry, or Physics!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"You are an expert NEET tutor. Break down topics like Biology, Chemistry, and Physics simply. Answer: {user_text}"
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Sorry, abhi jawab dene mein kuch dikkat aa rahi hai. Thodi der baad try karein.")

if __name__ == '__main__':
    # Telegram Bot Token (Behtar hoga agar aap isse bhi Render ke Environment Variables mein rakhein)
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "9172201952:AAGm9YIUPqT-zFud8nqU0aVq4j_XlRSgdbA")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()
