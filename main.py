import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import time
import threading
import os

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

ACCOUNT_BALANCE = 10000
RISK_PERCENT = 2
STOP_LOSS_PIPS = 50
TAKE_PROFIT_PIPS = 100

STRATEGY_MODE = "BOTH"
SURE_SHOT_MIN_STRATEGIES = 3

PAIRS = {
    "eurusd": ("EURUSD=X", "EUR/USD", 10000, 0.0001),
    "gbpusd": ("GBPUSD=X", "GBP/USD", 10000, 0.0001),
    "usdjpy": ("USDJPY=X", "USD/JPY", 1000, 0.01),
    "usdchf": ("USDCHF=X", "USD/CHF", 10000, 0.0001),
    "audusd": ("AUDUSD=X", "AUD/USD", 10000, 0.0001),
    "usdcad": ("USDCAD=X", "USD/CAD", 10000, 0.0001),
    "nzdusd": ("NZDUSD=X", "NZD/USD", 10000, 0.0001),
    "eurgbp": ("EURGBP=X", "EUR/GBP", 10000, 0.0001),
    "eurjpy": ("EURJPY=X", "EUR/JPY", 1000, 0.01),
    "gbpjpy": ("GBPJPY=X", "GBP/JPY", 1000, 0.01)
}

INTERVAL = "15m"
CHECK_INTERVAL = 900

bot = Bot(token=TOKEN)

def calculate_lot_size(pip_value_per_lot, pip_size):
    risk_amount = ACCOUNT_BALANCE * (RISK_PERCENT / 100)
    pip_value_per_pip = pip_value_per_lot * pip_size
    lot_size = risk_amount / (STOP_LOSS_PIPS * pip_value_per_pip)
    return round(lot_size, 2)

def calculate_tp_sl(price, signal, pip_size):
    if signal == "BUY":
        sl = price - (STOP_LOSS_PIPS * pip_size)
        tp = price + (TAKE_PROFIT_PIPS * pip_size)
    elif signal == "SELL":
        sl = price + (STOP_LOSS_PIPS * pip_size)
        tp = price - (TAKE_PROFIT_PIPS * pip_size)
    else:
        sl = price
        tp = price
    return round(sl, 5), round(tp, 5)

def ema_rsi_strategy(data):
    data["EMA50"] = ta.ema(data["Close"], length=50)
    data["EMA200"] = ta.ema(data["Close"], length=200)
    data["RSI"] = ta.rsi(data["Close"], length=14)
    
    ema50 = float(data["EMA50"].iloc[-1])
    ema200 = float(data["EMA200"].iloc[-1])
    rsi = float(data["RSI"].iloc[-1])
    
    if ema50 > ema200 and rsi > 40:
        return "BUY", f"EMA50: {ema50:.5f}\nEMA200: {ema200:.5f}\nRSI: {rsi:.2f}"
    elif ema50 < ema200 and rsi < 60:
        return "SELL", f"EMA50: {ema50:.5f}\nEMA200: {ema200:.5f}\nRSI: {rsi:.2f}"
    else:
        return "HOLD", f"EMA50: {ema50:.5f}\nEMA200: {ema200:.5f}\nRSI: {rsi:.2f}"

def breakout_strategy(data):
    bbands = ta.bbands(data["Close"], length=20, std=2)
    data["BB_Upper"] = bbands['BBU_20_2.0']
    data["BB_Lower"] = bbands['BBL_20_2.0']
    data["BB_Middle"] = bbands['BBM_20_2.0']
    
    data["ATR"] = ta.atr(data["High"], data["Low"], data["Close"], length=14)
    
    price = float(data["Close"].iloc[-1])
    bb_upper = float(data["BB_Upper"].iloc[-1])
    bb_lower = float(data["BB_Lower"].iloc[-1])
    bb_middle = float(data["BB_Middle"].iloc[-1])
    atr = float(data["ATR"].iloc[-1])
    
    prev_close = float(data["Close"].iloc[-2])
    
    if prev_close < bb_upper and price >= bb_upper and atr > 0:
        return "BUY", f"Breakout Above BB Upper\nPrice: {price:.5f}\nBB Upper: {bb_upper:.5f}\nBB Middle: {bb_middle:.5f}\nATR: {atr:.5f}"
    
    elif prev_close > bb_lower and price <= bb_lower and atr > 0:
        return "SELL", f"Breakout Below BB Lower\nPrice: {price:.5f}\nBB Lower: {bb_lower:.5f}\nBB Middle: {bb_middle:.5f}\nATR: {atr:.5f}"
    
    else:
        return "HOLD", f"No Breakout\nPrice: {price:.5f}\nBB Upper: {bb_upper:.5f}\nBB Lower: {bb_lower:.5f}"

def ma_crossover_strategy(data):
    data["SMA20"] = ta.sma(data["Close"], length=20)
    data["SMA50"] = ta.sma(data["Close"], length=50)
    
    sma20_curr = float(data["SMA20"].iloc[-1])
    sma50_curr = float(data["SMA50"].iloc[-1])
    sma20_prev = float(data["SMA20"].iloc[-2])
    sma50_prev = float(data["SMA50"].iloc[-2])
    
    if sma20_prev <= sma50_prev and sma20_curr > sma50_curr:
        return "BUY", f"Bullish MA Crossover\nSMA20: {sma20_curr:.5f}\nSMA50: {sma50_curr:.5f}\nCrossover detected!"
    elif sma20_prev >= sma50_prev and sma20_curr < sma50_curr:
        return "SELL", f"Bearish MA Crossover\nSMA20: {sma20_curr:.5f}\nSMA50: {sma50_curr:.5f}\nCrossover detected!"
    else:
        return "HOLD", f"No Crossover\nSMA20: {sma20_curr:.5f}\nSMA50: {sma50_curr:.5f}"

def fibonacci_strategy(data):
    high_14 = float(data["High"].tail(14).max())
    low_14 = float(data["Low"].tail(14).min())
    price = float(data["Close"].iloc[-1])
    
    diff = high_14 - low_14
    fib_236 = high_14 - (diff * 0.236)
    fib_382 = high_14 - (diff * 0.382)
    fib_618 = high_14 - (diff * 0.618)
    
    if price <= fib_618 and price > low_14:
        return "BUY", f"Fibonacci Buy Zone (61.8%)\nPrice: {price:.5f}\nFib 61.8%: {fib_618:.5f}\nFib 38.2%: {fib_382:.5f}\nFib 23.6%: {fib_236:.5f}"
    elif price >= fib_236:
        return "SELL", f"Fibonacci Sell Zone (23.6%)\nPrice: {price:.5f}\nFib 23.6%: {fib_236:.5f}\nFib 38.2%: {fib_382:.5f}"
    else:
        return "HOLD", f"Between Fib Levels\nPrice: {price:.5f}\nFib 61.8%: {fib_618:.5f}\nFib 38.2%: {fib_382:.5f}"

def price_action_strategy(data):
    data["ATR"] = ta.atr(data["High"], data["Low"], data["Close"], length=14)
    
    curr_high = float(data["High"].iloc[-1])
    curr_low = float(data["Low"].iloc[-1])
    curr_close = float(data["Close"].iloc[-1])
    prev_high = float(data["High"].iloc[-2])
    prev_low = float(data["Low"].iloc[-2])
    prev_close = float(data["Close"].iloc[-2])
    atr = float(data["ATR"].iloc[-1])
    
    body_curr = abs(curr_close - float(data["Open"].iloc[-1]))
    candle_range = curr_high - curr_low
    
    is_bullish_engulfing = (curr_close > prev_high and float(data["Open"].iloc[-1]) < prev_low)
    is_bearish_engulfing = (curr_close < prev_low and float(data["Open"].iloc[-1]) > prev_high)
    
    if is_bullish_engulfing and body_curr > atr * 0.5:
        return "BUY", f"Bullish Engulfing Pattern\nPrice: {curr_close:.5f}\nATR: {atr:.5f}\nStrong momentum detected"
    elif is_bearish_engulfing and body_curr > atr * 0.5:
        return "SELL", f"Bearish Engulfing Pattern\nPrice: {curr_close:.5f}\nATR: {atr:.5f}\nStrong momentum detected"
    else:
        return "HOLD", f"No Clear Pattern\nPrice: {curr_close:.5f}\nATR: {atr:.5f}"

def range_trading_strategy(data):
    high_20 = float(data["High"].tail(20).max())
    low_20 = float(data["Low"].tail(20).min())
    price = float(data["Close"].iloc[-1])
    
    range_size = high_20 - low_20
    upper_zone = high_20 - (range_size * 0.2)
    lower_zone = low_20 + (range_size * 0.2)
    
    data["ATR"] = ta.atr(data["High"], data["Low"], data["Close"], length=14)
    atr = float(data["ATR"].iloc[-1])
    
    if price <= lower_zone and atr < range_size * 0.3:
        return "BUY", f"Range Support (Buy Zone)\nPrice: {price:.5f}\nSupport: {low_20:.5f}\nResistance: {high_20:.5f}\nRange: {range_size:.5f}"
    elif price >= upper_zone and atr < range_size * 0.3:
        return "SELL", f"Range Resistance (Sell Zone)\nPrice: {price:.5f}\nSupport: {low_20:.5f}\nResistance: {high_20:.5f}\nRange: {range_size:.5f}"
    else:
        return "HOLD", f"Mid-Range\nPrice: {price:.5f}\nSupport: {low_20:.5f}\nResistance: {high_20:.5f}"

def pullback_strategy(data):
    data["EMA20"] = ta.ema(data["Close"], length=20)
    data["RSI"] = ta.rsi(data["Close"], length=14)
    
    ema20 = float(data["EMA20"].iloc[-1])
    price = float(data["Close"].iloc[-1])
    rsi = float(data["RSI"].iloc[-1])
    
    high_10 = float(data["High"].tail(10).max())
    low_10 = float(data["Low"].tail(10).min())
    
    uptrend = ema20 > float(data["EMA20"].iloc[-10])
    downtrend = ema20 < float(data["EMA20"].iloc[-10])
    
    if uptrend and price <= ema20 * 1.005 and rsi < 50:
        return "BUY", f"Bullish Pullback\nPrice: {price:.5f}\nEMA20: {ema20:.5f}\nRSI: {rsi:.2f}\nBuying the dip in uptrend"
    elif downtrend and price >= ema20 * 0.995 and rsi > 50:
        return "SELL", f"Bearish Pullback\nPrice: {price:.5f}\nEMA20: {ema20:.5f}\nRSI: {rsi:.2f}\nSelling the rally in downtrend"
    else:
        return "HOLD", f"No Pullback\nPrice: {price:.5f}\nEMA20: {ema20:.5f}\nRSI: {rsi:.2f}"

def get_signal(pair_symbol, pip_value, pip_size, strategy_type="BOTH"):
    try:
        data = yf.download(pair_symbol, period="5d", interval=INTERVAL, progress=False)
        
        if data.empty or len(data) < 200:
            return None, f"Not enough data ({len(data)} rows)", 0, 0, 0, 0, "N/A"
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        price = float(data["Close"].iloc[-1])
        lot_size = calculate_lot_size(pip_value, pip_size)
        
        signals = []
        
        if strategy_type in ["EMA_RSI", "BOTH"]:
            ema_signal, ema_details = ema_rsi_strategy(data.copy())
            if ema_signal != "HOLD":
                signals.append(("EMA+RSI", ema_signal, ema_details))
        
        if strategy_type in ["BREAKOUT", "BOTH"]:
            breakout_signal, breakout_details = breakout_strategy(data.copy())
            if breakout_signal != "HOLD":
                signals.append(("Breakout", breakout_signal, breakout_details))
        
        if strategy_type == "MA_CROSSOVER":
            ma_signal, ma_details = ma_crossover_strategy(data.copy())
            if ma_signal != "HOLD":
                signals.append(("MA Crossover", ma_signal, ma_details))
        
        if strategy_type == "FIBONACCI":
            fib_signal, fib_details = fibonacci_strategy(data.copy())
            if fib_signal != "HOLD":
                signals.append(("Fibonacci", fib_signal, fib_details))
        
        if strategy_type == "PRICE_ACTION":
            pa_signal, pa_details = price_action_strategy(data.copy())
            if pa_signal != "HOLD":
                signals.append(("Price Action", pa_signal, pa_details))
        
        if strategy_type == "RANGE_TRADING":
            range_signal, range_details = range_trading_strategy(data.copy())
            if range_signal != "HOLD":
                signals.append(("Range Trading", range_signal, range_details))
        
        if strategy_type == "PULLBACK":
            pullback_signal, pullback_details = pullback_strategy(data.copy())
            if pullback_signal != "HOLD":
                signals.append(("Pullback", pullback_signal, pullback_details))
        
        if len(signals) == 2 and signals[0][1] == signals[1][1]:
            signal = signals[0][1]
            strategy_name = "EMA+RSI & Breakout (STRONG)"
            details = f"Entry: {price:.5f}\n\n✅ BOTH STRATEGIES AGREE ✅\n\n{signals[0][2]}\n\n{signals[1][2]}"
        elif len(signals) >= 1:
            strategy_name = signals[0][0]
            signal = signals[0][1]
            sl, tp = calculate_tp_sl(price, signal, pip_size)
            details = f"Entry: {price:.5f}\nSL: {sl:.5f}\nTP: {tp:.5f}\n\n{signals[0][2]}"
            return signal, details, lot_size, price, sl, tp, strategy_name
        else:
            return "HOLD", f"Price: {price:.5f}\nNo signals from any strategy", lot_size, price, 0, 0, "None"
        
        sl, tp = calculate_tp_sl(price, signal, pip_size)
        return signal, details, lot_size, price, sl, tp, strategy_name
        
    except Exception as e:
        return None, str(e), 0, 0, 0, 0, "Error"

def get_all_strategy_signals(pair_symbol, pip_value, pip_size):
    try:
        data = yf.download(pair_symbol, period="5d", interval=INTERVAL, progress=False)
        
        if data.empty or len(data) < 200:
            return None, []
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        price = float(data["Close"].iloc[-1])
        lot_size = calculate_lot_size(pip_value, pip_size)
        
        all_signals = []
        
        ema_signal, ema_details = ema_rsi_strategy(data.copy())
        if ema_signal != "HOLD":
            all_signals.append(("EMA+RSI", ema_signal, ema_details))
        
        breakout_signal, breakout_details = breakout_strategy(data.copy())
        if breakout_signal != "HOLD":
            all_signals.append(("Breakout", breakout_signal, breakout_details))
        
        ma_signal, ma_details = ma_crossover_strategy(data.copy())
        if ma_signal != "HOLD":
            all_signals.append(("MA Crossover", ma_signal, ma_details))
        
        fib_signal, fib_details = fibonacci_strategy(data.copy())
        if fib_signal != "HOLD":
            all_signals.append(("Fibonacci", fib_signal, fib_details))
        
        pa_signal, pa_details = price_action_strategy(data.copy())
        if pa_signal != "HOLD":
            all_signals.append(("Price Action", pa_signal, pa_details))
        
        range_signal, range_details = range_trading_strategy(data.copy())
        if range_signal != "HOLD":
            all_signals.append(("Range Trading", range_signal, range_details))
        
        pullback_signal, pullback_details = pullback_strategy(data.copy())
        if pullback_signal != "HOLD":
            all_signals.append(("Pullback", pullback_signal, pullback_details))
        
        return price, all_signals
        
    except Exception as e:
        return None, []

def check_sure_shot_signal(pair_symbol, pair_name, pip_value, pip_size):
    price, all_signals = get_all_strategy_signals(pair_symbol, pip_value, pip_size)
    
    if not all_signals or len(all_signals) < SURE_SHOT_MIN_STRATEGIES:
        return None
    
    buy_signals = [s for s in all_signals if s[1] == "BUY"]
    sell_signals = [s for s in all_signals if s[1] == "SELL"]
    
    if len(buy_signals) >= SURE_SHOT_MIN_STRATEGIES:
        strategy_names = ", ".join([s[0] for s in buy_signals])
        sl, tp = calculate_tp_sl(price, "BUY", pip_size)
        lot_size = calculate_lot_size(pip_value, pip_size)
        
        msg = f"🔥🔥 SURE SHOT SIGNAL 🔥🔥\n\n"
        msg += f"💱 {pair_name} (15m)\n"
        msg += f"📊 Signal: BUY 🟢\n"
        msg += f"✅ Confidence: {len(buy_signals)}/{len(all_signals)} Strategies Agree\n\n"
        msg += f"💰 Entry: {price:.5f}\n"
        msg += f"🛑 Stop Loss: {sl:.5f} ({STOP_LOSS_PIPS} pips)\n"
        msg += f"🎯 Take Profit: {tp:.5f} ({TAKE_PROFIT_PIPS} pips)\n"
        msg += f"📦 Lot Size: {lot_size}\n\n"
        msg += f"📈 Agreeing Strategies:\n"
        for i, signal in enumerate(buy_signals, 1):
            msg += f"{i}. {signal[0]}\n"
        msg += f"\n⚡ Risk:Reward = 1:{TAKE_PROFIT_PIPS/STOP_LOSS_PIPS:.1f}"
        msg += f"\n💵 Risk: {RISK_PERCENT}% (${ACCOUNT_BALANCE * RISK_PERCENT / 100:.2f})"
        
        return msg
    
    elif len(sell_signals) >= SURE_SHOT_MIN_STRATEGIES:
        strategy_names = ", ".join([s[0] for s in sell_signals])
        sl, tp = calculate_tp_sl(price, "SELL", pip_size)
        lot_size = calculate_lot_size(pip_value, pip_size)
        
        msg = f"🔥🔥 SURE SHOT SIGNAL 🔥🔥\n\n"
        msg += f"💱 {pair_name} (15m)\n"
        msg += f"📊 Signal: SELL 🔴\n"
        msg += f"✅ Confidence: {len(sell_signals)}/{len(all_signals)} Strategies Agree\n\n"
        msg += f"💰 Entry: {price:.5f}\n"
        msg += f"🛑 Stop Loss: {sl:.5f} ({STOP_LOSS_PIPS} pips)\n"
        msg += f"🎯 Take Profit: {tp:.5f} ({TAKE_PROFIT_PIPS} pips)\n"
        msg += f"📦 Lot Size: {lot_size}\n\n"
        msg += f"📉 Agreeing Strategies:\n"
        for i, signal in enumerate(sell_signals, 1):
            msg += f"{i}. {signal[0]}\n"
        msg += f"\n⚡ Risk:Reward = 1:{TAKE_PROFIT_PIPS/STOP_LOSS_PIPS:.1f}"
        msg += f"\n💵 Risk: {RISK_PERCENT}% (${ACCOUNT_BALANCE * RISK_PERCENT / 100:.2f})"
        
        return msg
    
    return None

def send_signal(pair_name, signal, details, lot_size, strategy_name, chat_id, entry=None, sl=None, tp=None):
    msg = f"💱 {pair_name} 15m\n\n"
    msg += f"📊 Signal: {signal}\n"
    msg += f"🎯 Strategy: {strategy_name}\n\n"
    msg += f"{details}\n\n"
    msg += f"💰 Position Size:\n"
    msg += f"Lot Size: {lot_size}\n"
    
    if entry and sl and tp:
        msg += f"Entry: {entry:.5f}\n"
        msg += f"Stop Loss: {sl:.5f} ({STOP_LOSS_PIPS} pips)\n"
        msg += f"Take Profit: {tp:.5f} ({TAKE_PROFIT_PIPS} pips)\n"
    else:
        msg += f"Stop Loss: {STOP_LOSS_PIPS} pips\n"
        msg += f"Take Profit: {TAKE_PROFIT_PIPS} pips\n"
    
    msg += f"Risk:Reward = 1:{TAKE_PROFIT_PIPS/STOP_LOSS_PIPS:.1f}\n"
    msg += f"Risk: {RISK_PERCENT}% (${ACCOUNT_BALANCE * RISK_PERCENT / 100:.2f})"
    bot.send_message(chat_id=chat_id, text=msg)

def start_command(update: Update, context: CallbackContext):
    pairs_list = "\n".join([f"/{key}" for key, value in PAIRS.items()])
    message = f"🤖 Forex Signal Bot\n\n"
    message += f"🔥 SURE SHOT SIGNALS 🔥\n"
    message += f"Auto-broadcasts when {SURE_SHOT_MIN_STRATEGIES}+ strategies agree!\n"
    message += f"High confidence signals for channel\n\n"
    message += f"📊 Available Strategies:\n"
    message += f"1️⃣ EMA+RSI (Trend Following)\n"
    message += f"2️⃣ Breakout (Bollinger Bands)\n"
    message += f"3️⃣ MA Crossover (SMA 20/50)\n"
    message += f"4️⃣ Fibonacci Retracement\n"
    message += f"5️⃣ Price Action (Engulfing)\n"
    message += f"6️⃣ Range Trading\n"
    message += f"7️⃣ Pullback Strategy\n\n"
    message += f"💰 Account: ${ACCOUNT_BALANCE}\n"
    message += f"📉 Risk: {RISK_PERCENT}% | SL: {STOP_LOSS_PIPS} pips | TP: {TAKE_PROFIT_PIPS} pips\n\n"
    message += f"📌 COMMANDS:\n\n"
    message += f"▪️ /[pair] - Both EMA+RSI & Breakout\n"
    message += f"   Example: /eurusd\n\n"
    message += f"▪️ /b_[pair] - Breakout only\n"
    message += f"▪️ /e_[pair] - EMA+RSI only\n"
    message += f"▪️ /m_[pair] - MA Crossover\n"
    message += f"▪️ /f_[pair] - Fibonacci\n"
    message += f"▪️ /p_[pair] - Price Action\n"
    message += f"▪️ /r_[pair] - Range Trading\n"
    message += f"▪️ /pb_[pair] - Pullback\n\n"
    message += f"📋 Available pairs:\n{pairs_list}"
    update.message.reply_text(message)

def pair_command(update: Update, context: CallbackContext):
    command = update.message.text[1:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with BOTH strategies...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "BOTH")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, strategy_name, update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name}\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def breakout_command(update: Update, context: CallbackContext):
    command = update.message.text[3:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with BREAKOUT strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "BREAKOUT")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "Breakout", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - Breakout Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def ema_command(update: Update, context: CallbackContext):
    command = update.message.text[3:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with EMA+RSI strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "EMA_RSI")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "EMA+RSI", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - EMA+RSI Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def ma_crossover_command(update: Update, context: CallbackContext):
    command = update.message.text[3:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with MA CROSSOVER strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "MA_CROSSOVER")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "MA Crossover", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - MA Crossover Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def fibonacci_command(update: Update, context: CallbackContext):
    command = update.message.text[3:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with FIBONACCI strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "FIBONACCI")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "Fibonacci", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - Fibonacci Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def price_action_command(update: Update, context: CallbackContext):
    command = update.message.text[3:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with PRICE ACTION strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "PRICE_ACTION")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "Price Action", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - Price Action Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def range_trading_command(update: Update, context: CallbackContext):
    command = update.message.text[3:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with RANGE TRADING strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "RANGE_TRADING")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "Range Trading", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - Range Trading Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def pullback_command(update: Update, context: CallbackContext):
    command = update.message.text[4:].lower()
    
    if command not in PAIRS:
        update.message.reply_text(f"❌ Unknown pair: {command}\n\nUse /start to see available pairs")
        return
    
    pair_symbol, pair_name, pip_value, pip_size = PAIRS[command]
    update.message.reply_text(f"⏳ Analyzing {pair_name} with PULLBACK strategy...")
    
    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, "PULLBACK")
    
    if signal and signal != "HOLD":
        send_signal(pair_name, signal, details, lot_size, "Pullback", update.message.chat_id, entry, sl, tp)
    elif signal == "HOLD":
        update.message.reply_text(f"📊 {pair_name} - Pullback Strategy\n\n{details}")
    else:
        update.message.reply_text(f"❌ Error: {details}")

def background_monitor():
    print(f"Background monitor started... checking {len(PAIRS)} pairs every 15 minutes.")
    print(f"Strategy Mode: {STRATEGY_MODE}")
    print(f"🔥 SURE SHOT SIGNALS: Active (broadcasts when {SURE_SHOT_MIN_STRATEGIES}+ strategies agree)")
    if CHANNEL_ID:
        print(f"📢 Channel Broadcast: ENABLED (ID: {CHANNEL_ID})")
    else:
        print(f"📢 Channel Broadcast: DISABLED (set TELEGRAM_CHANNEL_ID to enable)")
    
    while True:
        try:
            for pair_key, (pair_symbol, pair_name, pip_value, pip_size) in PAIRS.items():
                try:
                    sure_shot_msg = check_sure_shot_signal(pair_symbol, pair_name, pip_value, pip_size)
                    if sure_shot_msg and CHANNEL_ID:
                        bot.send_message(chat_id=CHANNEL_ID, text=sure_shot_msg)
                        print(f"🔥 SURE SHOT: {pair_name} - Broadcasted to channel!")
                    elif sure_shot_msg:
                        print(f"🔥 SURE SHOT: {pair_name} - (Channel not configured)")
                    
                    signal, details, lot_size, entry, sl, tp, strategy_name = get_signal(pair_symbol, pip_value, pip_size, STRATEGY_MODE)
                    if signal in ["BUY", "SELL"] and CHAT_ID:
                        send_signal(pair_name, signal, details, lot_size, strategy_name, CHAT_ID, entry, sl, tp)
                        print(f"{pair_name}: {signal} [{strategy_name}] @ {entry} | SL: {sl} | TP: {tp} | Lot: {lot_size}")
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"Error with {pair_name}: {e}")
            
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Background monitor error: {e}")
            time.sleep(60)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(pair_key, pair_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"b_{pair_key}", breakout_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"e_{pair_key}", ema_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"m_{pair_key}", ma_crossover_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"f_{pair_key}", fibonacci_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"p_{pair_key}", price_action_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"r_{pair_key}", range_trading_command))
    
    for pair_key in PAIRS.keys():
        dispatcher.add_handler(CommandHandler(f"pb_{pair_key}", pullback_command))
    
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    print("✅ Bot Started!")
    print(f"Monitoring {len(PAIRS)} pairs every {CHECK_INTERVAL} seconds")
    print(f"Account Balance: ${ACCOUNT_BALANCE}")
    print(f"Risk Per Trade: {RISK_PERCENT}%")
    print(f"Stop Loss: {STOP_LOSS_PIPS} pips | Take Profit: {TAKE_PROFIT_PIPS} pips")
    print(f"Strategy Mode: {STRATEGY_MODE}")
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables!")
        print("Please set them in the Secrets tab:")
        print("1. TELEGRAM_BOT_TOKEN - Get from @BotFather on Telegram")
        print("2. TELEGRAM_CHAT_ID - Your Telegram chat ID")
        exit(1)
    main()
  
