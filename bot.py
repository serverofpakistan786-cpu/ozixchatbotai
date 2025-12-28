# Fix for Python 3.13 imghdr error
import sys
try:
    import imghdr
except ModuleNotFoundError:
    class ImghdrDummy:
        def what(self, *args):
            return None
    sys.modules['imghdr'] = ImghdrDummy()

if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    import collections
    setattr(collections, "MutableMapping", collections.abc.MutableMapping)

import os
import logging
from datetime import datetime

import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv

from database import MongoDB

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "@YourUsername")

# Group and Channel Links
GROUP_LINK = os.getenv("GROUP_LINK", "https://t.me/your_group")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")
DEVELOPER_LINK = f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}"

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

# Ayesha's Personality Prompt
AYESHA_PERSONALITY = """You are Ayesha, a friendly, intelligent and empathetic Indian female AI assistant. You speak in natural Hinglish (Hindi + English). Keep responses short and conversational in Hinglish."""

class AyeshaBot:
    def __init__(self):
        if MONGO_URI:
            try:
                self.db = MongoDB()
            except:
                self.db = None
        else:
            self.db = None
    
    def create_welcome_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
            [InlineKeyboardButton("👨‍💻 Developer", url=DEVELOPER_LINK)],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def generate_response(self, message):
        if not model:
            return "AI service unavailable. Try later."
        try:
            prompt = f"{AYESHA_PERSONALITY}\nUser: {message}\nAyesha:"
            response = model.generate_content(prompt)
            return response.text
        except:
            return "Sorry, technical issue. Try again."
    
    def start(self, update, context):
        user = update.effective_user
        text = f"Namaste {user.first_name}! I'm Ayesha. How can I help?"
        update.message.reply_text(text, reply_markup=self.create_welcome_keyboard())
        
        if self.db:
            self.db.create_user({
                "user_id": user.id,
                "first_name": user.first_name,
                "username": user.username,
                "joined": datetime.now()
            })
    
    def handle_message(self, update, context):
        user_msg = update.message.text
        response = self.generate_response(user_msg)
        update.message.reply_text(response)
    
    def button_callback(self, update, context):
        query = update.callback_query
        query.answer()
        
        if query.data == "about":
            query.edit_message_text("Ayesha Bot v1.0 - Your AI friend")
        elif query.data == "help":
            query.edit_message_text("Just type your message!")

def main():
    bot = AyeshaBot()
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", bot.start))
    dp.add_handler(CallbackQueryHandler(bot.button_callback))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    logger.info("Starting Ayesha Bot...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
