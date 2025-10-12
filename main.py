import os
import asyncio
import json
import httpx
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- SubscriberManager Class (merged) ---
class SubscriberManager:
    def __init__(self, filepath: str = 'subscribers.json'):
        self.filepath = filepath
        self.subscribers: Set[int] = self._load_subscribers()
    
    def _load_subscribers(self) -> Set[int]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    return set(map(int, data.get('subscribers', [])))
            except Exception as e:
                print(f"Error loading subscribers: {e}")
        return set()
    
    def _save_subscribers(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump({'subscribers': list(self.subscribers)}, f, indent=2)
        except Exception as e:
            print(f"Error saving subscribers: {e}")
    
    def add_subscriber(self, user_id: int) -> bool:
        if user_id not in self.subscribers:
            self.subscribers.add(user_id)
            self._save_subscribers()
            return True
        return False
    
    def remove_subscriber(self, user_id: int) -> bool:
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self._save_subscribers()
            return True
        return False
    
    def is_subscribed(self, user_id: int) -> bool:
        return user_id in self.subscribers
    
    def get_all_subscribers(self) -> Set[int]:
        return self.subscribers.copy()
    
    def get_subscriber_count(self) -> int:
        return len(self.subscribers)

# --- ForexSignalGenerator Class (merged and updated) ---
class ForexSignalGenerator:
    def __init__(self, alpha_vantage_key: str):
        self.api_key = alpha_vantage_key
        self.base_url = 'https://www.alphavantage.co/query'
        self.cache = {}
        self.cache_duration = 7200 
        self.last_request_time = 0
        self.min_request_interval = 12
        
    async def _make_request(self, params: Dict) -> Optional[Dict]:
        if not self.api_key:
            print("ERROR: ALPHA_VANTAGE_API_KEY not set")
            return None
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await self._wait(self.min_request_interval - time_since_last)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params['apikey'] = self.api_key
                response = await client.get(self.base_url, params=params)
                self.last_request_time = time.time()
                data = response.json()
                
                if 'Note' in data:
                    print(f"API Rate limit warning: {data['Note']}")
                    return None
                    
                return data
        except Exception as e:
            print(f"Error making request: {e}")
            return None
    
    async def _wait(self, seconds: float):
        await asyncio.sleep(seconds)
    
    def _get_cache_key(self, function: str, symbol: str) -> str:
        return f"{function}_{symbol}"
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        cached_time = self.cache[key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_duration
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Dict]:
        cache_key = self._get_cache_key('RATE', f"{from_currency}{to_currency}")
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency,
        }
        
        data = await self._make_request(params)
        if not data:
            return None
        
        if 'Realtime Currency Exchange Rate' in data:
            rate_data = data['Realtime Currency Exchange Rate']
            result = {
                'pair': f"{from_currency}/{to_currency}",
                'rate': float(rate_data['5. Exchange Rate']),
                'bid': float(rate_data.get('8. Bid Price', rate_data['5. Exchange Rate'])),
                'ask': float(rate_data.get('9. Ask Price', rate_data['5. Exchange Rate'])),
                'time': rate_data['6. Last Refreshed']
            }
            
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
        
        return None
    
    async def get_ema(self, from_currency: str, to_currency: str, time_period: int, interval: str = '15min') -> Optional[float]:
        symbol = f"{from_currency}{to_currency}"
        cache_key = self._get_cache_key(f'EMA{time_period}', symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        params = {
            'function': 'EMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close',
        }
        
        data = await self._make_request(params)
        if not data:
            return None
        
        if 'Technical Analysis: EMA' in data:
            ema_data = data['Technical Analysis: EMA']
            latest_time = list(ema_data.keys())[0]
            result = float(ema_data[latest_time]['EMA'])
            
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
        
        return None
    
    async def get_rsi(self, from_currency: str, to_currency: str, interval: str = '15min') -> Optional[float]:
        symbol = f"{from_currency}{to_currency}"
        cache_key = self._get_cache_key('RSI', symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': interval,
            'time_period': 14,
            'series_type': 'close',
        }
        
        data = await self._make_request(params)
        if not data:
            return None
        
        if 'Technical Analysis: RSI' in data:
            rsi_data = data['Technical Analysis: RSI']
            latest_time = list(rsi_data.keys())[0]
            result = float(rsi_data[latest_time]['RSI'])
            
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
        
        return None
    
    async def get_macd(self, from_currency: str, to_currency: str, interval: str = '15min') -> Optional[Dict]:
        symbol = f"{from_currency}{to_currency}"
        cache_key = self._get_cache_key('MACD', symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': interval,
            'series_type': 'close',
        }
        
        data = await self._make_request(params)
        if not data:
            return None
        
        if 'Technical Analysis: MACD' in data:
            macd_data = data['Technical Analysis: MACD']
            latest_time = list(macd_data.keys())[0]
            result = {
                'macd': float(macd_data[latest_time]['MACD']),
                'signal': float(macd_data[latest_time]['MACD_Signal']),
                'histogram': float(macd_data[latest_time]['MACD_Hist'])
            }
            
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
        
        return None
    
    def determine_pip_value(self, pair: str) -> float:
        return 0.01 if 'JPY' in pair else 0.0001
        
    def calculate_entry_sl_tp(self, current_rate: float, signal_type: str, pip_value: float = 0.0001) -> Dict:
        SL_PIPS = 30
        TP_PIPS = 60
        entry = current_rate
        
        if signal_type == "BUY":
            sl = entry - (SL_PIPS * pip_value)
            tp = entry + (TP_PIPS * pip_value)
        elif signal_type == "SELL":
            sl = entry + (SL_PIPS * pip_value)
            tp = entry - (TP_PIPS * pip_value)
        else:
            sl = entry
            tp = entry
            
        return {
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'sl_pips': SL_PIPS,
            'tp_pips': TP_PIPS
        }

    def calculate_lot_size(self, sl_pips: int) -> Dict:
        ACCOUNT_BALANCE = 10000.00
        RISK_PERCENT = 2.0
        
        risk_amount = ACCOUNT_BALANCE * (RISK_PERCENT / 100)
        
        if sl_pips > 0:
            lot_size = round(risk_amount / (sl_pips * 10), 2)
        else:
            lot_size = 0.01
            
        return {
            'lot_size': lot_size,
            'risk_percent': RISK_PERCENT,
            'risk_amount': round(risk_amount, 2),
            'account_balance': ACCOUNT_BALANCE
        }


    async def generate_signal(self, from_currency: str, to_currency: str) -> Dict:
        rate = await self.get_exchange_rate(from_currency, to_currency)
        
        if not rate:
            return {'success': False, 'message': '❌ Unable to fetch forex data. Check API key or rate limits.'}
        
        # Fetch indicators
        ema50 = await self.get_ema(from_currency, to_currency, 50)
        ema200 = await self.get_ema(from_currency, to_currency, 200)
        rsi = await self.get_rsi(from_currency, to_currency)
        macd = await self.get_macd(from_currency, to_currency)
        
        signal_type = "NEUTRAL"
        confidence = "LOW"
        reasons = []
        
        # Determine signal based on EMA Cross + RSI
        if ema50 and ema200 and rsi:
            if ema50 > ema200 and rsi < 50:
                signal_type = "BUY"
                reasons.append("EMA50 > EMA200 (Uptrend)")
                reasons.append(f"RSI below 50 ({rsi:.2f})")
                confidence = "HIGH"
            elif ema50 < ema200 and rsi > 50:
                signal_type = "SELL"
                reasons.append("EMA50 < EMA200 (Downtrend)")
                reasons.append(f"RSI above 50 ({rsi:.2f})")
                confidence = "HIGH"
            elif rsi < 30: 
                signal_type = "BUY"
                reasons.append(f"RSI oversold ({rsi:.2f})")
                confidence = "MEDIUM"
            elif rsi > 70: 
                signal_type = "SELL"
                reasons.append(f"RSI overbought ({rsi:.2f})")
                confidence = "MEDIUM"
        
        # Trading Levels Calculation
        pair_key = f"{from_currency}/{to_currency}"
        pip_value = self.determine_pip_value(pair_key)
        levels = self.calculate_entry_sl_tp(rate['rate'], signal_type, pip_value)
        lot_size_info = self.calculate_lot_size(levels['sl_pips'])

        return {
            'success': True,
            'pair': pair_key,
            'timeframe': '15min',
            'current_rate': rate['rate'],
            'bid': rate['bid'],
            'ask': rate['ask'],
            'signal': signal_type,
            'confidence': confidence,
            'rsi': rsi,
            'macd': macd,
            'ema50': ema50,
            'ema200': ema200,
            'reasons': reasons,
            'entry': levels['entry'],
            'sl': levels['sl'],
            'tp': levels['tp'],
            'sl_pips': levels['sl_pips'],
            'tp_pips': levels['tp_pips'],
            'lot_size': lot_size_info['lot_size'],
            'risk_percent': lot_size_info['risk_percent'],
            'risk_amount': lot_size_info['risk_amount'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def get_popular_pairs_signals(self) -> List[Dict]:
        pairs = [
            ('EUR', 'USD'),
            ('GBP', 'USD'),
            ('USD', 'JPY'),
            ('AUD', 'USD')
        ]
        
        signals = []
        for from_curr, to_curr in pairs:
            signal = await self.generate_signal(from_curr, to_curr)
            if signal['success']:
                signals.append(signal)
        
        return signals
    
    def format_signal_message(self, signal: Dict) -> str:
        if not signal['success']:
            return f"❌ {signal['message']}"
        
        emoji_map = {'BUY': '🟢', 'SELL': '🔴', 'NEUTRAL': '⚪'}
        confidence_emoji = {'HIGH': '⭐⭐⭐', 'MEDIUM': '⭐⭐', 'LOW': '⭐'}
        
        decimal_places = 5
        if 'JPY' in signal['pair']:
            decimal_places = 3
            
        rate_format = f".{decimal_places}f"
        
        def format_indicator(value, fmt_str):
            if value is None:
                return 'N/A'
            return f"{value:{fmt_str}}"

        message = f"""
{emoji_map.get(signal['signal'], '⚪')} **{signal['pair']} LIVE SIGNAL**

💱 {signal['pair']} {signal.get('timeframe', '15min')}
📊 **Signal:** **{signal['signal']}**
🎯 **Strategy:** EMA+RSI
"""
        
        # --- TRADING LEVELS ---
        if signal['signal'] != 'NEUTRAL':
            message += f"""
🎯 **Entry Price:** **{signal['entry']:{rate_format}}**
🛑 **Stop Loss (SL):** {signal['sl']:{rate_format}}
✅ **Take Profit (TP):** {signal['tp']:{rate_format}}
"""
        else:
            message += f"""
⚠️ **Neutral/Hold:** No strong signal detected.
"""
        
        # --- INDICATOR VALUES (Corrected to use helper function) ---
        message += "\n"
        message += f"EMA50: {format_indicator(signal['ema50'], rate_format)}"
        message += f"\nEMA200: {format_indicator(signal['ema200'], rate_format)}"
        message += f"\nRSI: {format_indicator(signal['rsi'], '.2f')}"
        
        # --- POSITION SIZE ---
        if signal['signal'] != 'NEUTRAL':
            message += f"""

💰 **Position Size (2.0% Risk on $10,000):**
Lot Size: **{signal['lot_size']}**
Stop Loss: {signal['sl_pips']} pips
Take Profit: {signal['tp_pips']} pips
Risk:Reward = **1:2**
Risk: {signal['risk_percent']:.1f}% (${signal['risk_amount']:.2f})
"""
        
        # --- FOOTER ---
        message += f"""
        
💱 **Current Rate:** {signal['current_rate']:{rate_format}}
📈 **Bid/Ask:** {signal['bid']:{rate_format}} / {signal['ask']:{rate_format}}
"""
        
        message += f"\n\n💪 **Confidence:** {signal['confidence']} {confidence_emoji.get(signal['confidence'], '')}"
        
        if signal.get('reasons'):
            message += f"\n💡 **Reasons:**\n" + "\n".join([f"  • {r}" for r in signal['reasons']])
        
        message += f"\n\n🕐 **Time:** {signal['timestamp']}"
        
        return message

# --- Global Initialization & Main Logic ---

# --- HARDCODED KEYS AND IDs ---
TELEGRAM_BOT_TOKEN = '6223574146:AAGEuRVuEoQyp4NqbshxMNANPYCLVzShNDU' 
ALPHA_VANTAGE_API_KEY = 'NSDEIO7LL029Z6BR'
ADMIN_USER_ID = 5828410338 
BROADCAST_CHANNEL_ID = -1002962477294 

# 💸 CRYPTOCURRENCY PAYMENT DETAILS (for manual subscription)
BNB_ADDRESS = '0xf46dB5B8A38f4cE3F7C287Ca7Cd406F2AB29F369'
BTC_ADDRESS = 'Bc1pxak5m8x696h7f2vjw077lxrkgltufl5wcggx5gjp0skvkeypg3msw85xg0'
ETH_ADDRESS = '0xf46dB5B8A38f4cE3F7C287Ca7Cd406F2AB29F369'
USDT_ADDRESS = '0xf46dB5B8A38f4cE3F7C287Ca7Cd406F2AB29F369'

PAYMENT_INSTRUCTIONS = f"""
💰 **Subscription Required: $10 (Monthly)**

Please send $10 USD equivalent to ONE of the following addresses (Always confirm the network!):

1. 🟡 **BNB (BEP-20):**
   `{BNB_ADDRESS}`

2. ₿ **Bitcoin (BTC):**
   `{BTC_ADDRESS}`

3. ♦️ **Ethereum (ETH/ERC20):**
   `{ETH_ADDRESS}`

4. ₮ **USDT (ERC20):**
   `{USDT_ADDRESS}`
   
**IMPORTANT:** Once funds are sent, send your transaction hash/receipt to the Admin (me) to get your subscription activated!
"""
# ------------------------------------------

# Initialize managers globally (must be done after class definitions)
signal_generator = ForexSignalGenerator(alpha_vantage_key=ALPHA_VANTAGE_API_KEY)
subscriber_manager = SubscriberManager()

# --- HANDLER FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    welcome_message = """
🤖 **Welcome to Forex Signal Bot!** 📈

I provide real-time forex trading signals based on technical analysis (RSI & MACD indicators).

**Available Commands:**
/start - Show this welcome message
/subscribe - Subscribe to automatic signals (PAID for general users, FREE for Admin)
/unsubscribe - Unsubscribe from automatic signals
/signals - Get current forex signals for major pairs
/signal <FROM> <TO> - Get signal for specific pair (e.g., /signal EUR USD)

**Note:** Signals are for educational purposes only. Always do your own research before trading!
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user: return
    user_id = update.effective_user.id
    
    if subscriber_manager.is_subscribed(user_id):
        await update.message.reply_text("You're already subscribed to signals!", parse_mode='Markdown')
        return

    is_admin = (user_id == ADMIN_USER_ID)
    
    if is_admin:
        subscription_status = "✅ Admin Access Granted (FREE)."
    else:
        # Standard user flow: Present payment wall
        payment_message = PAYMENT_INSTRUCTIONS
        await update.message.reply_text(payment_message, parse_mode='Markdown')
        return
    
    if subscriber_manager.add_subscriber(user_id):
        message = f"""
✅ **You're now subscribed!**

{subscription_status}

You will receive forex signals automatically (if the host supports the scheduler).
To unsubscribe, use /unsubscribe
"""
        await update.message.reply_text(message, parse_mode='Markdown')

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user: return
    user_id = update.effective_user.id
    if subscriber_manager.remove_subscriber(user_id):
        await update.message.reply_text("✅ You've been unsubscribed from automatic signals.", parse_mode='Markdown')
    else:
        await update.message.reply_text("You're not currently subscribed.", parse_mode='Markdown')

async def get_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    await update.message.reply_text("🔄 Fetching latest forex signals... Please wait.", parse_mode='Markdown')
    signals = await signal_generator.get_popular_pairs_signals() 
    
    if not signals:
        await update.message.reply_text("❌ Unable to fetch forex data. Check API key or rate limits.", parse_mode='Markdown')
        return
    
    header = f"📊 **FOREX SIGNALS UPDATE**\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    await update.message.reply_text(header, parse_mode='Markdown')
    for signal in signals:
        message = signal_generator.format_signal_message(signal)
        await update.message.reply_text(message, parse_mode='Markdown')
        await asyncio.sleep(1)


async def get_specific_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not context.args: return
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
    if not signal['success']:
        await update.message.reply_text(signal['message'], parse_mode='Markdown')
        return
    message = signal_generator.format_signal_message(signal)
    await update.message.reply_text(message, parse_mode='Markdown')

async def add_subscriber_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access Denied. Only the Admin can use this command.", parse_mode='Markdown')
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: `/addsub <user_id>`\nExample: `/addsub 123456789`", parse_mode='Markdown')
        return

    try:
        user_to_add = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID. Please provide a numeric Telegram User ID.", parse_mode='Markdown')
        return

    if subscriber_manager.add_subscriber(user_to_add):
        await update.message.reply_text(f"✅ **Subscription Activated!**\nUser ID `{user_to_add}` has been successfully added.", parse_mode='Markdown')
        
        try:
             await context.bot.send_message(
                chat_id=user_to_add,
                text="🎉 **Welcome to the service!** Your paid subscription has been activated by the Admin. Use /signals to get started.",
                parse_mode='Markdown'
            )
        except Exception:
            pass
            
    else:
        await update.message.reply_text(f"❌ User ID `{user_to_add}` is already subscribed.", parse_mode='Markdown')


async def broadcast_signals(context: ContextTypes.DEFAULT_TYPE):
    # This function is currently UNUSED because the job queue is disabled.
    pass 

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user: return
    
    # --- ADMIN ACCESS CHECK ---
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Command not found.", parse_mode='Markdown')
        return 
    # --- END ADMIN ACCESS CHECK ---

    subscriber_count = subscriber_manager.get_subscriber_count()
    is_subscribed = subscriber_manager.is_subscribed(update.effective_user.id)
    
    status_message = f"""
📊 **Bot Status (ADMIN VIEW)**

👥 Total Subscribers: {subscriber_count}
📱 Your Status: {"✅ Subscribed (Admin)" if update.effective_user.id == ADMIN_USER_ID else "✅ Subscribed" if is_subscribed else "❌ Not Subscribed"}

📡 Broadcast Frequency: Every 1 hour (DISABLED due to missing library)
💾 API Cache Duration: 2 hours
🔄 API Rate Limit: 12s between requests

The bot is running core functionality.
"""
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def send_sure_shot_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_user.id != ADMIN_USER_ID:
        # Hide the command for non-admins
        await update.message.reply_text("❌ Command not found.", parse_mode='Markdown')
        return 
        
    await update.message.reply_text("🔎 Checking for High Confidence signals for channel broadcast...", parse_mode='Markdown')

    signals = await signal_generator.get_popular_pairs_signals() 
    sent_count = 0
    
    for signal in signals:
        if signal['confidence'] == 'HIGH' and signal['signal'] != 'NEUTRAL':
            message = signal_generator.format_signal_message(signal)
            
            try:
                await context.bot.send_message(
                    chat_id=BROADCAST_CHANNEL_ID,
                    text="🚨 **SURE SHOT SIGNAL ALERT!** 🚨\n\n" + message,
                    parse_mode='Markdown'
                )
                sent_count += 1
                await asyncio.sleep(1)
            except Exception as e:
                error_msg = f"❌ Error sending signal to channel {BROADCAST_CHANNEL_ID}: {e}"
                print(error_msg)
                await update.message.reply_text(error_msg)
    
    if sent_count > 0:
        await update.message.reply_text(f"✅ Successfully broadcast {sent_count} HIGH CONFIDENCE signals to the channel.", parse_mode='Markdown')
    else:
        await update.message.reply_text("No HIGH CONFIDENCE signals found at this moment for broadcast.", parse_mode='Markdown')

# --- Main Execution ---
def main():
    if not TELEGRAM_BOT_TOKEN or not ALPHA_VANTAGE_API_KEY:
        print("FATAL ERROR: API keys are empty.")
        return
    
    print("Starting Forex Signal Bot...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("signals", get_signals))
    application.add_handler(CommandHandler("signal", get_specific_signal))
    
    # --- Secret Admin Commands ---
    application.add_handler(CommandHandler("status", status)) 
    application.add_handler(CommandHandler("sureshot", send_sure_shot_to_channel)) 
    application.add_handler(CommandHandler("addsub", add_subscriber_admin)) 
    
    # --- Job Queue Setup DISABLED ---
    # The job queue code is commented out because it requires the missing 'pytz' library.
    # job_queue = application.job_queue
    # if job_queue:
    #     job_queue.run_repeating(broadcast_signals, interval=3600, first=10)
    
    print("⚠️ WARNING: Automatic 1-hour signal broadcast is disabled.")
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print(f"📊 Current subscribers: {subscriber_manager.get_subscriber_count()}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
