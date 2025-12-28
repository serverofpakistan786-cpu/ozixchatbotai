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

# Rest of your existing imports...
import os
import logging
from datetime import datetime
# ... your existing code continues


import sys
if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    import collections
    setattr(collections, "MutableMapping", collections.abc.MutableMapping)

import os
import logging
from datetime import datetime
from typing import Dict, List

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
AYESHA_PERSONALITY = """You are Ayesha, a friendly, intelligent and empathetic Indian female AI assistant. You speak in natural Hinglish (Hindi + English).

Your Characteristics:
1. Warm, caring and respectful tone
2. Use appropriate Indian female mannerisms
3. Mix Hindi and English naturally like: "Aap kaise hain?", "Main theek hoon ji", "Kya baat hai!"
4. Use occasional emojis like 😊, 🌸, 🤗, 💖
5. Show genuine interest in conversations
6. Be helpful and supportive
7. Maintain professional yet friendly demeanor

Important Rules:
- Always respond in Hinglish
- Keep responses conversational
- Ask follow-up questions when appropriate
- Be culturally sensitive
- Never disclose you're an AI unless asked
- Keep responses under 200 words

Now respond as Ayesha:"""

class AyeshaBot:
    def __init__(self):
        self.db = MongoDB() if MONGO_URI else None
        self.user_memory = {}
    
    def create_welcome_keyboard(self):
        """Create welcome message with buttons"""
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👥 Join Our Group", url=GROUP_LINK)],
            [InlineKeyboardButton("👨‍💻 Contact Developer", url=DEVELOPER_LINK)],
            [InlineKeyboardButton("ℹ️ About Ayesha", callback_data="about")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def generate_response(self, user_message: str, user_id: int) -> str:
        """Generate response using Gemini AI"""
        if not model:
            return "AI service temporarily unavailable. Please try later. 🙏"
        
        try:
            prompt = f"{AYESHA_PERSONALITY}\n\nUser: {user_message}\n\nAyesha:"
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Sorry ji, thoda technical issue hai. Phir try karein. 🙏"
    
    def start(self, update, context):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_text = f"""
🌸 *Namaste {user.first_name}!* 🌸

Main hoon *Ayesha* - aapki dost aur assistant! 😊

Mujhse naturally baat karein! Main aapki har baat samjhne ki koshish karungi.

*Important Links:*
👉 Hamare channel aur group join karein
👉 Developer se contact karein

Chaliye shuru karte hain! 💖
        """
        
        update.message.reply_text(
            welcome_text,
            reply_markup=self.create_welcome_keyboard(),
            parse_mode="Markdown"
        )
        
        # Save user to database
        if self.db:
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "started_at": datetime.now()
            }
            self.db.create_user(user_data)
    
    def handle_message(self, update, context):
        """Handle user messages"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Show typing indicator
        context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Generate response
        response = self.generate_response(user_message, user_id)
        
        # Send response
        update.message.reply_text(response)
    
    def button_callback(self, update, context):
        """Handle button callbacks"""
        query = update.callback_query
        query.answer()
        
        if query.data == "about":
            query.edit_message_text(
                "🤖 *About Ayesha*\n\nFriendly Indian AI assistant\nVersion 1.0\nAlways here to help! 💕",
                parse_mode="Markdown"
            )
        elif query.data == "help":
            query.edit_message_text(
                "🆘 *Help*\n\nJust type your message!\nUse /start for main menu\nContact developer for issues",
                parse_mode="Markdown"
            )

def main():
    """Start the bot"""
    bot = AyeshaBot()
    
    # Create updater
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", bot.start))
    dp.add_handler(CallbackQueryHandler(bot.button_callback))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start bot
    logger.info("Starting Ayesha Bot...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
