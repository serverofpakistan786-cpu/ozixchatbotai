import os
import logging
from datetime import datetime

import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

from database import MongoDB

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

class AyeshaBot:
    def __init__(self):
        self.db = MongoDB() if MONGO_URI else None
    
    def create_welcome_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/your_channel")],
            [InlineKeyboardButton("👥 Join Group", url="https://t.me/your_group")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/developer")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def generate_response(self, message):
        if not model:
            return "AI service unavailable."
        try:
            prompt = f"You are Ayesha, a friendly Indian AI assistant. Respond in Hinglish.\nUser: {message}\nAyesha:"
            response = model.generate_content(prompt)
            return response.text
        except:
            return "Sorry, technical issue."
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = f"Namaste {user.first_name}! I'm Ayesha."
        await update.message.reply_text(text, reply_markup=self.create_welcome_keyboard())
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = self.generate_response(update.message.text)
        await update.message.reply_text(response)

def main():
    bot = AyeshaBot()
    
    app = Application.builder().token(API_TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("Starting Ayesha Bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
