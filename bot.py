import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from forex_signals import ForexSignalGenerator
from subscribers import SubscriberManager

signal_generator = ForexSignalGenerator()
subscriber_manager = SubscriberManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    welcome_message = """
🤖 **Welcome to Forex Signal Bot!** 📈

I provide real-time forex trading signals based on technical analysis (RSI & MACD indicators).

**Available Commands:**
/start - Show this welcome message
/subscribe - Subscribe to automatic signals (every 8 hours)
/unsubscribe - Unsubscribe from automatic signals
/signals - Get current forex signals for major pairs
/signal <FROM> <TO> - Get signal for specific pair (e.g., /signal EUR USD)
/status - Check bot status and your subscription

**Note:** Signals are for educational purposes only. Always do your own research before trading!
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    
    if subscriber_manager.add_subscriber(user_id):
        message = """
✅ **You're now subscribed!**

You'll receive forex signals automatically every 8 hours for major currency pairs (EUR/USD, GBP/USD, USD/JPY, AUD/USD).

To unsubscribe, use /unsubscribe
"""
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("You're already subscribed to signals!", parse_mode='Markdown')

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    
    if subscriber_manager.remove_subscriber(user_id):
        await update.message.reply_text("✅ You've been unsubscribed from automatic signals.", parse_mode='Markdown')
    else:
        await update.message.reply_text("You're not currently subscribed.", parse_mode='Markdown')

async def get_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    await update.message.reply_text("🔄 Fetching latest forex signals... Please wait.", parse_mode='Markdown')
    
    signals = await signal_generator.get_popular_pairs_signals()
    
    if not signals:
        await update.message.reply_text("❌ Unable to fetch signals at the moment. Please try again later.", parse_mode='Markdown')
        return
    
    header = f"📊 **FOREX SIGNALS UPDATE**\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    await update.message.reply_text(header, parse_mode='Markdown')
    
    for signal in signals:
        message = signal_generator.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='Markdown')
        await asyncio.sleep(1)

async def get_specific_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not context.args:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Please specify currency pair.\n\nUsage: /signal <FROM> <TO>\nExample: /signal EUR USD",
            parse_mode='Markdown'
        )
        return
    
    from_currency = context.args[0].upper()
    to_currency = context.args[1].upper()
    
    await update.message.reply_text(f"🔄 Fetching signal for {from_currency}/{to_currency}...", parse_mode='Markdown')
    
    signal = await signal_generator.generate_signal(from_currency, to_currency)
    message = signal_generator.format_signal_message(signal)
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def broadcast_signals(context: ContextTypes.DEFAULT_TYPE):
    subscribers = subscriber_manager.get_all_subscribers()
    
    if not subscribers:
        print("No subscribers to broadcast to.")
        return
    
    signals = await signal_generator.get_popular_pairs_signals()
    
    if not signals:
        print("Unable to fetch signals for broadcast.")
        return
    
    header = f"🔔 **AUTOMATED FOREX SIGNALS**\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for user_id in subscribers:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=header,
                parse_mode='Markdown'
            )
            
            for signal in signals:
                message = signal_generator.format_signal_message(signal)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                await asyncio.sleep(0.5)
            
            print(f"Broadcast sent to user {user_id}")
            
        except Exception as e:
            print(f"Error broadcasting to user {user_id}: {e}")
            if "Forbidden" in str(e):
                subscriber_manager.remove_subscriber(user_id)
                print(f"Removed blocked user {user_id}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    
    subscriber_count = subscriber_manager.get_subscriber_count()
    is_subscribed = subscriber_manager.is_subscribed(update.effective_user.id)
    
    status_message = f"""
📊 **Bot Status**

👥 Total Subscribers: {subscriber_count}
📱 Your Status: {"✅ Subscribed" if is_subscribed else "❌ Not Subscribed"}

📡 Broadcast Frequency: Every 8 hours
💾 Cache Duration: 12 hours  
🔄 API Rate Limit: 15s between requests

The bot broadcasts signals to all subscribers optimized for API usage.
"""
    await update.message.reply_text(status_message, parse_mode='Markdown')

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    print("Starting Forex Signal Bot...")
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("signals", get_signals))
    application.add_handler(CommandHandler("signal", get_specific_signal))
    application.add_handler(CommandHandler("status", status))
    
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(broadcast_signals, interval=28800, first=60)
    
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print(f"📊 Current subscribers: {subscriber_manager.get_subscriber_count()}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
  
