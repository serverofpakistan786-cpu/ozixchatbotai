from flask import Flask, request
import os
from bot_ayesha import AyeshaBot, API_TOKEN
from telegram.ext import Application

app = Flask(__name__)

# Initialize bot
bot = AyeshaBot()
application = Application.builder().token(API_TOKEN).build()

# Set up handlers (same as in main bot)
application.add_handler(CommandHandler("start", bot.start))
application.add_handler(CommandHandler("help", lambda u, c: bot.button_callback(u, c)))
application.add_handler(CommandHandler("stats", bot.stats_command))
application.add_handler(CommandHandler("broadcast", bot.broadcast_command))
application.add_handler(CallbackQueryHandler(bot.button_callback))
application.add_handler(MessageHandler(
    filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
    bot.handle_private_message
))
application.add_handler(MessageHandler(
    filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
    bot.handle_group_message
))
application.add_error_handler(bot.error_handler)

# Initialize application
application.initialize()

@app.route('/')
def home():
    return "🌸 Ayesha Bot is Running! 🌸"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.update_queue.put(update)
    return 'OK'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/webhook"
    application.bot.set_webhook(webhook_url)
    return f"Webhook set to: {webhook_url}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
