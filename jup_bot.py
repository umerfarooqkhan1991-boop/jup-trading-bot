import os
import pandas as pd
import requests
import ccxt
from ta.momentum import RSIIndicator, StochasticOscillator
import datetime

# Get Discord webhook from GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK')
BOT_NAME = "JUP Bot"

def send_discord_alert(message, alert_type="INFO"):
    """Send alert to Discord with formatted message"""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Discord webhook not configured")
        return False
    
    try:
        # Create embedded message
        color = 16711680 if "OVERSOLD" in alert_type else 32768 if "OVERBOUGHT" in alert_type else 3447003
        
        embed = {
            "title": f"🚨 {alert_type}",
            "description": message,
            "color": color,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "footer": {
                "text": BOT_NAME
            },
            "fields": [
                {
                    "name": "Time (UTC)",
                    "value": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "inline": True
                }
            ]
        }
        
        payload = {
            "embeds": [embed],
            "username": BOT_NAME
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            print(f"✅ {alert_type} alert sent to Discord")
            return True
        else:
            print(f"❌ Discord error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False

def get_jup_data():
    """Get JUP data from OKX exchange"""
    try:
        # Initialize OKX for perpetual futures (works on GitHub servers)
        exchange = ccxt.okx({
            'options': {
                'defaultType': 'swap'  # Perpetual futures
            },
            'timeout': 30000  # 30 second timeout
        })
        
        # Fetch JUP/USDT perpetual futures data (5-minute intervals)
        ohlcv = exchange.fetch_ohlcv('JUP/USDT:USDT', '15m', limit=100)
        
        # Create DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col])
        
        print(f"✅ Data fetched successfully")
        print(f"📊 Data points: {len(df)}")
        print(f"💰 Latest price: ${df['close'].iloc[-1]:.4f}")
        
        return df
        
    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        return None

def calculate_indicators(df):
    """Calculate RSI and Stochastic RSI indicators"""
    try:
        # Calculate RSI (14 period)
        df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        
        # Calculate Stochastic RSI
        stoch = StochasticOscillator(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=14,
            smooth_window=3
        )
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        # Get latest values
        latest = df.iloc[-1]
        
        indicators = {
            'price': latest['close'],
            'rsi': latest['rsi'],
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'timestamp': datetime.datetime.fromtimestamp(latest['timestamp']/1000)
        }
        
        print(f"📈 Indicators calculated")
        print(f"📉 RSI: {indicators['rsi']:.2f}")
        print(f"📊 Stochastic %K: {indicators['stoch_k']:.2f}")
        print(f"📊 Stochastic %D: {indicators['stoch_d']:.2f}")
        
        return indicators
        
    except Exception as e:
        print(f"❌ Indicator calculation error: {e}")
        return None

def check_alerts(indicators):
    """Check for RSI + Stochastic RSI combo alerts"""
    alerts = []
    
    rsi = indicators['rsi']
    stoch_k = indicators['stoch_k']
    price = indicators['price']
    
    # Strong Oversold: RSI < 30 AND Stochastic %K < 10
    if rsi < 30 and stoch_k < 10:
        alerts.append({
            'type': 'STRONG OVERSOLD',
            'message': f"**JUP PERPETUAL FUTURES - STRONG OVERSOLD!**\n\n"
                      f"💰 **Price**: ${price:.4f}\n"
                      f"📉 **RSI**: {rsi:.2f} (< 30)\n"
                      f"📊 **Stochastic %K**: {stoch_k:.2f} (< 10)\n\n"
                      f"🎯 **Potential LONG opportunity**",
            'condition': 'OVERSOLD'
        })
    
    # Strong Overbought: RSI > 70 AND Stochastic %K > 90
    elif rsi > 70 and stoch_k > 90:
        alerts.append({
            'type': 'STRONG OVERBOUGHT',
            'message': f"**JUP PERPETUAL FUTURES - STRONG OVERBOUGHT!**\n\n"
                      f"💰 **Price**: ${price:.4f}\n"
                      f"📈 **RSI**: {rsi:.2f} (> 70)\n"
                      f"📊 **Stochastic %K**: {stoch_k:.2f} (> 90)\n\n"
                      f"⚠️ **Potential SHORT opportunity**",
            'condition': 'OVERBOUGHT'
        })
    
    # Weak signals (only one indicator triggered)
    elif rsi < 30:
        alerts.append({
            'type': 'RSI OVERSOLD',
            'message': f"**RSI Oversold Signal**\n"
                      f"Price: ${price:.4f}\n"
                      f"RSI: {rsi:.2f} (< 30)\n"
                      f"👀 Watch for Stochastic confirmation",
            'condition': 'WATCH'
        })
    
    elif stoch_k < 20:
        alerts.append({
            'type': 'STOCHASTIC OVERSOLD',
            'message': f"**Stochastic Oversold Signal**\n"
                      f"Price: ${price:.4f}\n"
                      f"Stochastic %K: {stoch_k:.2f} (< 20)\n"
                      f"👀 Watch for RSI confirmation",
            'condition': 'WATCH'
        })
    
    return alerts

def main():
    """Main function"""
    print("=" * 60)
    print("🎯 JUP Trading Bot - GitHub Actions")
    print(f"⏰ Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check if Discord webhook is set
    if not DISCORD_WEBHOOK_URL:
        print("❌ WARNING: DISCORD_WEBHOOK not set in GitHub Secrets")
        print("❌ Alerts will not be sent to Discord")
    
    # Step 1: Get data
    print("\n📥 Step 1: Fetching JUP data from OKX...")
    df = get_jup_data()
    if df is None:
        print("❌ Failed to get data, exiting")
        return
    
    # Step 2: Calculate indicators
    print("\n📊 Step 2: Calculating indicators...")
    indicators = calculate_indicators(df)
    if indicators is None:
        print("❌ Failed to calculate indicators, exiting")
        return
    
    # Step 3: Check alerts
    print("\n🔔 Step 3: Checking for alerts...")
    alerts = check_alerts(indicators)
    
    # Step 4: Send alerts
    if alerts:
        print(f"\n🚨 Found {len(alerts)} alert(s):")
        for alert in alerts:
            print(f"   • {alert['type']}")
            send_discord_alert(alert['message'], alert['type'])
    else:
        print("\n✅ No alerts triggered")
        # Send status update (optional, remove if too many messages)
        status_msg = f"**JUP Status Update**\nPrice: ${indicators['price']:.4f}\nRSI: {indicators['rsi']:.2f}\nStochastic: {indicators['stoch_k']:.2f}"
        send_discord_alert(status_msg, "STATUS UPDATE")
    
    print("\n" + "=" * 60)
    print("✅ Bot execution completed")
    print(f"⏰ Finished: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
