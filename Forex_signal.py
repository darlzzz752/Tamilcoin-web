import httpx
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import lru_cache
import time

class ForexSignalGenerator:
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.cache = {}
        self.cache_duration = 300
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
        import asyncio
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
            'apikey': self.api_key
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
            'apikey': self.api_key
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
            'apikey': self.api_key
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
    
    async def generate_signal(self, from_currency: str, to_currency: str) -> Dict:
        rate = await self.get_exchange_rate(from_currency, to_currency)
        
        if not rate:
            return {
                'success': False,
                'message': 'Unable to fetch forex data. Check API key or rate limits.'
            }
        
        rsi = await self.get_rsi(from_currency, to_currency)
        macd = await self.get_macd(from_currency, to_currency)
        
        signal_type = "NEUTRAL"
        confidence = "LOW"
        reasons = []
        
        if rsi:
            if rsi < 30:
                signal_type = "BUY"
                reasons.append(f"RSI oversold ({rsi:.2f})")
                confidence = "MEDIUM"
            elif rsi > 70:
                signal_type = "SELL"
                reasons.append(f"RSI overbought ({rsi:.2f})")
                confidence = "MEDIUM"
        
        if macd:
            if macd['macd'] > macd['signal'] and macd['histogram'] > 0:
                if signal_type == "BUY" or signal_type == "NEUTRAL":
                    signal_type = "BUY"
                    reasons.append("MACD bullish crossover")
                    if rsi and rsi < 40:
                        confidence = "HIGH"
            elif macd['macd'] < macd['signal'] and macd['histogram'] < 0:
                if signal_type == "SELL" or signal_type == "NEUTRAL":
                    signal_type = "SELL"
                    reasons.append("MACD bearish crossover")
                    if rsi and rsi > 60:
                        confidence = "HIGH"
        
        return {
            'success': True,
            'pair': rate['pair'],
            'current_rate': rate['rate'],
            'bid': rate['bid'],
            'ask': rate['ask'],
            'signal': signal_type,
            'confidence': confidence,
            'rsi': rsi,
            'macd': macd,
            'reasons': reasons,
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
        
        emoji_map = {
            'BUY': '🟢',
            'SELL': '🔴',
            'NEUTRAL': '⚪'
        }
        
        confidence_emoji = {
            'HIGH': '⭐⭐⭐',
            'MEDIUM': '⭐⭐',
            'LOW': '⭐'
        }
        
        message = f"""
{emoji_map.get(signal['signal'], '⚪')} **{signal['pair']} SIGNAL**

📊 **Signal:** {signal['signal']}
💪 **Confidence:** {signal['confidence']} {confidence_emoji.get(signal['confidence'], '')}

💱 **Current Rate:** {signal['current_rate']:.5f}
📈 **Bid:** {signal['bid']:.5f}
📉 **Ask:** {signal['ask']:.5f}
"""
        
        if signal.get('rsi'):
            message += f"\n📐 **RSI (14):** {signal['rsi']:.2f}"
        
        if signal.get('macd'):
            message += f"\n📊 **MACD:** {signal['macd']['macd']:.6f}"
            message += f"\n🔔 **Signal Line:** {signal['macd']['signal']:.6f}"
        
        if signal.get('reasons'):
            message += f"\n\n💡 **Reasons:**\n" + "\n".join([f"  • {r}" for r in signal['reasons']])
        
        message += f"\n\n🕐 **Time:** {signal['timestamp']}"
        
        return message
          
