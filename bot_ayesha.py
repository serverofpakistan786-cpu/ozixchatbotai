import os
import logging
from datetime import datetime
from typing import Dict, List

import google.generativeai as genai
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    CallbackQueryHandler
)
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
OWNER_ID = int(os.getenv("OWNER_ID", 0))  # Your Telegram ID
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "@YourUsername")

# Group and Channel Links
GROUP_LINK = os.getenv("GROUP_LINK", "https://t.me/your_group")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")
DEVELOPER_LINK = f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

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

Example Responses:
- "Namaste! Aap kaise hain aaj? 😊"
- "Wah! Ye to bahut interesting hai. Aap aur details bataiye."
- "Main aapki madad karne ke liye yahan hoon. Kya aap bata sakte hain ki aapko kis cheez mein help chahiye?"
- "Achha samjhi. Main aapko is bare mein jaankari dene ki koshish karoongi."

Now respond as Ayesha:"""

class AyeshaBot:
    def __init__(self):
        self.db = MongoDB()
        self.model = genai.GenerativeModel('gemini-pro')
        self.user_sessions: Dict[int, List] = {}
    
    async def generate_response(self, user_message: str, user_id: int) -> str:
        """Generate response using Gemini AI"""
        try:
            # Get conversation history from MongoDB
            history = self.db.get_conversation_history(user_id, limit=5)
            
            # Format conversation history
            conversation_history = ""
            for msg in reversed(history):  # Reverse to get chronological order
                role = "User" if msg["role"] == "user" else "Ayesha"
                conversation_history += f"{role}: {msg['message']}\n"
            
            # Create prompt with personality and history
            prompt = f"""{AYESHA_PERSONALITY}

Conversation History:
{conversation_history}

User: {user_message}

Ayesha (responding in Hinglish):"""
            
            # Generate response
            response = await self.model.generate_content_async(prompt)
            
            # Clean response
            ai_response = response.text.strip()
            
            # Save conversation to database
            self.db.add_conversation(user_id, "user", user_message)
            self.db.add_conversation(user_id, "assistant", ai_response)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return "Maaf kijiye, thoda technical issue aa raha hai. Kya aap thodi der baad phir try kar sakte hain? 🙏"
    
    def create_welcome_keyboard(self):
        """Create welcome message with image and buttons"""
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👥 Join Our Group", url=GROUP_LINK)],
            [InlineKeyboardButton("👨‍💻 Contact Developer", url=DEVELOPER_LINK)],
            [InlineKeyboardButton("ℹ️ About Ayesha", callback_data="about")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with image and buttons"""
        user = update.effective_user
        
        # Save user to database
        if not self.db.get_user(user.id):
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
                "is_bot": user.is_bot,
                "started_at": datetime.now()
            }
            self.db.create_user(user_data)
        
        # Welcome message with Ayesha's introduction
        welcome_text = f"""
🌸 *Namaste {user.first_name}!* 🌸

Main hoon *Ayesha* - aapki dost aur assistant! 😊

Mujhse naturally baat karein, bilkul aap kisi dost se baat karte hain waise! Main aapki har baat samjhne ki koshish karungi aur aapki help karungi.

*Meri specialities:*
• 🗣️ Natural Hinglish conversations
• 💭 Personal memory (main aapko yaad rakhungi!)
• 🌟 24/7 available
• 🤗 Emotional support
• 📚 Knowledge sharing

*Important Links:*
👉 Hamare channel aur group join karein updates ke liye
👉 Developer se direct contact karein agar koi help chahiye

Chaliye shuru karte hain! Aap aaj kaise hain? 💖
        """
        
        # Send welcome message with image
        try:
            # You can replace with your bot's photo URL
            photo_url = "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400"
            await update.message.reply_photo(
                photo=photo_url,
                caption=welcome_text,
                reply_markup=self.create_welcome_keyboard(),
                parse_mode="Markdown"
            )
        except:
            # If photo fails, send text only
            await update.message.reply_text(
                welcome_text,
                reply_markup=self.create_welcome_keyboard(),
                parse_mode="Markdown"
            )
        
        # Notify owner about new user
        await self.notify_owner_new_user(update, user)
    
    async def notify_owner_new_user(self, update: Update, user):
        """Notify owner about new user"""
        if OWNER_ID:
            notification = f"""
🆕 *New User Started Ayesha Bot* 🆕

*User Info:*
👤 Name: {user.first_name} {user.last_name or ''}
🆔 ID: `{user.id}`
📛 Username: @{user.username or 'N/A'}
📅 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

*Bot Statistics:*
👥 Total Users: {self.db.get_all_users()}
            """
            
            try:
                await update.application.bot.send_message(
                    chat_id=OWNER_ID,
                    text=notification,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify owner: {e}")
    
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle private messages"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Generate response
        response = await self.generate_response(user_message, user_id)
        
        # Send response
        await update.message.reply_text(response)
    
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group messages when mentioned"""
        if update.message.text and "@" + context.bot.username in update.message.text:
            user_message = update.message.text.replace("@" + context.bot.username, "").strip()
            user_id = update.effective_user.id
            
            if user_message:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action="typing"
                )
                
                response = await self.generate_response(user_message, user_id)
                await update.message.reply_text(response)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "about":
            about_text = """
*About Ayesha Bot* 🤖✨

*Name:* Ayesha
*Personality:* Friendly Indian Female AI
*Language:* Hinglish (Hindi + English)
*Creator:* Private Developer
*Version:* 2.0

*Features:*
• 🧠 AI-powered conversations using Google Gemini
• 💾 MongoDB memory for personalized chats
• 👥 Group & channel integration
• 📊 User tracking system
• 🔔 Owner notifications

*Technical Stack:*
• Python + Telegram Bot API
• Google Gemini AI
• MongoDB Database
• Render.com Hosting

Main hamesha aapki help ke liye tayyar hoon! 💕
            """
            
            keyboard = [
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]
            ]
            
            await query.edit_message_text(
                about_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        elif query.data == "help":
            help_text = """
*Help Guide - Ayesha Bot* 🆘

*How to Use:*
1. *Private Chat:* Direct message karein
2. *Group Chat:* @ayeshabot mention karein
3. *Commands:*
   /start - Bot shuru karein
   /help - Yeh message
   /stats - Bot statistics (owner only)
   /broadcast - Message sabko bhejein (owner only)

*Features Access:*
• Channel join button - Latest updates
• Group join button - Community discussions
• Developer contact - Direct help
• Memory system - Personalized conversations

*Need More Help?*
Developer se contact karein: @YourUsername

Aap kisi bhi waqt mujhse baat kar sakte hain! 😊
            """
            
            keyboard = [
                [InlineKeyboardButton("Join Channel 📢", url=CHANNEL_LINK)],
                [InlineKeyboardButton("Contact Developer 👨‍💻", url=DEVELOPER_LINK)],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
            ]
            
            await query.edit_message_text(
                help_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        elif query.data == "back_to_menu":
            # Show original welcome message
            user = query.from_user
            welcome_text = f"""
🌸 Welcome back, {user.first_name}! 🌸

Aapko kis cheez mein help chahiye?

Choose an option below:"""
            
            keyboard = self.create_welcome_keyboard()
            await query.edit_message_text(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics (Owner only)"""
        user_id = update.effective_user.id
        
        if user_id == OWNER_ID:
            total_users = self.db.get_all_users()
            
            stats_text = f"""
*📊 Ayesha Bot Statistics*

*User Statistics:*
👥 Total Users: {total_users}
📅 Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

*Database Info:*
🗃️ MongoDB: Connected ✅
💾 Conversations: Stored
👤 User Data: Saved

*Bot Status:*
🟢 Online & Active
🔄 Memory: Working
🤖 AI: Gemini Pro

*Quick Actions:*
Use /broadcast to message all users
            """
            
            await update.message.reply_text(stats_text, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ This command is for owner only.")
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users (Owner only)"""
        user_id = update.effective_user.id
        
        if user_id == OWNER_ID:
            if not context.args:
                await update.message.reply_text("Usage: /broadcast Your message here")
                return
            
            message = " ".join(context.args)
            broadcast_text = f"""
*📢 Announcement from Developer*

{message}

*~ Ayesha Bot Team*
            """
            
            # Get all users from database (you'll need to implement this method)
            # This is a simplified version
            await update.message.reply_text(
                f"Broadcast message prepared. Would send to all users:\n\n{broadcast_text}"
            )
        else:
            await update.message.reply_text("⚠️ This command is for owner only.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Notify owner about error
        if OWNER_ID:
            try:
                error_msg = f"""
❌ *Bot Error Occurred*

*Error:* {context.error}
*Update:* {update}
*Time:* {datetime.now()}
                """
                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=error_msg,
                    parse_mode="Markdown"
                )
            except:
                pass

def main():
    """Start the bot"""
    bot = AyeshaBot()
    
    # Create Application
    application = Application.builder().token(API_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", lambda u, c: bot.button_callback(u, c)))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("broadcast", bot.broadcast_command))
    
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
        bot.handle_private_message
    ))
    
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        bot.handle_group_message
    ))
    
    # Error handler
    application.add_error_handler(bot.error_handler)
    
    # Start the bot
    logger.info("Starting Ayesha Bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
