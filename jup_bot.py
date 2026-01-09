import os
import requests
import ccxt
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
import time
import traceback

print("=== JUP TRADING BOT START ===")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Get Discord webhook from environment
webhook = os.environ.get("DISCORD_WEBHOOK")
if webhook:
    print("✅ Discord webhook configured")
else:
    print("⚠️ No Discord webhook (set DISCORD_WEBHOOK secret)")

try:
    # Initialize OKX exchange for perpetual futures
    print("📡 Connecting to OKX API...")
    exchange = ccxt.okx({
        'options': {
            'defaultType': 'swap'  # For perpetual futures
        },
        'timeout': 30000,  # 30 second timeout
        'enableRateLimit': True,
    })
    
    # Fetch JUP/USDT perpetual futures data
    print("📥 Fetching JUP data...")
    ohlcv = exchange.fetch_ohlcv('JUP/USDT:USDT', '15m', limit=100)
    
    # Create DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col])
    
    # Get current price
    current_price = df['close'].iloc[-1]
    print(f"💰 JUP Price: ${current_price:.4f}")
    
    # Calculate RSI (14 period)
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    current_rsi = df['rsi'].iloc[-1]
    print(f"📉 RSI (14): {current_rsi:.2f}")
    
    # Calculate Stochastic RSI
    stoch = StochasticOscillator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14,
        smooth_window=3
    )
    df['stoch_k'] = stoch.stoch()
    current_stoch = df['stoch_k'].iloc[-1]
    print(f"📊 Stochastic %K: {current_stoch:.2f}")
    
    # Additional info
    price_change_24h = ((current_price - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
    print(f"📈 24h Change: {price_change_24h:+.2f}%")
    
    # Check alerts
    alert_triggered = False
    message = ""
    
    # STRONG OVERSOLD: RSI < 30 AND Stochastic < 10
    if current_rsi < 30 and current_stoch < 10:
        message = f"""🚨 **JUP PERPETUAL - STRONG OVERSOLD!**

💰 **Price**: ${current_price:.4f}
📉 **RSI**: {current_rsi:.2f} (< 30)
📊 **Stochastic**: {current_stoch:.2f} (< 10)
📈 **24h Change**: {price_change_24h:+.2f}%

🎯 **Potential LONG opportunity**
⚠️ Always use proper risk management!"""
        alert_type = "STRONG OVERSOLD"
        alert_triggered = True
        print("🚨 STRONG OVERSOLD condition met!")
    
    # STRONG OVERBOUGHT: RSI > 70 AND Stochastic > 90
    elif current_rsi > 70 and current_stoch > 90:
        message = f"""🚨 **JUP PERPETUAL - STRONG OVERBOUGHT!**

💰 **Price**: ${current_price:.4f}
📈 **RSI**: {current_rsi:.2f} (> 70)
📊 **Stochastic**: {current_stoch:.2f} (> 90)
📈 **24h Change**: {price_change_24h:+.2f}%

⚠️ **Potential SHORT opportunity**
⚠️ Always use proper risk management!"""
        alert_type = "STRONG OVERBOUGHT"
        alert_triggered = True
        print("🚨 STRONG OVERBOUGHT condition met!")
    
    # WEAK SIGNALS (only one indicator)
    elif current_rsi < 30:
        message = f"""📊 **JUP - RSI Approaching Oversold**

💰 **Price**: ${current_price:.4f}
📉 **RSI**: {current_rsi:.2f} (Approaching 20)
📊 **Stochastic**: {current_stoch:.2f}
📈 **24h Change**: {price_change_24h:+.2f}%

👀 **Watch for Stochastic confirmation**"""
        alert_type = "RSI WARNING"
        alert_triggered = True
        print("📊 RSI approaching oversold")
    
    elif current_stoch < 20:
        message = f"""📊 **JUP - Stochastic Approaching Oversold**

💰 **Price**: ${current_price:.4f}
📉 **RSI**: {current_rsi:.2f}
📊 **Stochastic**: {current_stoch:.2f} (Approaching 15)
📈 **24h Change**: {price_change_24h:+.2f}%

👀 **Watch for RSI confirmation**"""
        alert_type = "STOCHASTIC WARNING"
        alert_triggered = True
        print("📊 Stochastic approaching oversold")
    
    else:
        message = f"""✅ **JUP Status Update**

💰 **Price**: ${current_price:.4f}
📉 **RSI**: {current_rsi:.2f}
📊 **Stochastic**: {current_stoch:.2f}
📈 **24h Change**: {price_change_24h:+.2f}%

✅ **No strong signals detected**
Next check in 15 minutes ⏰"""
        alert_type = "STATUS"
        print("✅ No alerts triggered")
    
    # Send to Discord if webhook exists
    if webhook:
        try:
            response = requests.post(webhook, json={"content": message}, timeout=10)
            if response.status_code == 204:
                print(f"✅ {alert_type} message sent to Discord")
            else:
                print(f"❌ Discord error: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to send to Discord: {e}")
    else:
        print(f"📝 {alert_type} Message Ready (no webhook)")
    
    print("=== JUP TRADING BOT END ===")
    print("✅ Bot execution completed successfully")

except ccxt.NetworkError as e:
    error_msg = f"❌ Network error: {str(e)[:100]}"
    print(error_msg)
    if webhook:
        requests.post(webhook, json={"content": f"❌ JUP Bot Network Error\n{error_msg}"})
    
except ccxt.ExchangeError as e:
    error_msg = f"❌ Exchange error: {str(e)[:100]}"
    print(error_msg)
    if webhook:
        requests.post(webhook, json={"content": f"❌ JUP Bot Exchange Error\n{error_msg}"})
    
except Exception as e:
    error_msg = f"❌ Unexpected error: {str(e)[:100]}"
    print(error_msg)
    print(traceback.format_exc())
    if webhook:
        requests.post(webhook, json={"content": f"❌ JUP Bot Error\n{error_msg}"})
