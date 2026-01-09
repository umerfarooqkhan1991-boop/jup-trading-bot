import os
import requests
import random
import time

print("=== JUP TRADING BOT START ===")

# Get Discord webhook from environment
webhook = os.environ.get("DISCORD_WEBHOOK")
if webhook:
    print("✅ Discord webhook configured")
else:
    print("⚠️ No Discord webhook (set DISCORD_WEBHOOK secret)")

# Simulate data (you'll replace with real API later)
price = round(random.uniform(0.80, 0.90), 4)
rsi = round(random.uniform(20, 80), 2)
stoch = round(random.uniform(20, 80), 2)

print(f"💰 JUP Price: ${price}")
print(f"📉 RSI: {rsi}")
print(f"📊 Stochastic: {stoch}")

# Check alerts
if rsi < 30 and stoch < 20:
    message = f"🚨 JUP OVERSOLD ALERT!\nPrice: ${price}\nRSI: {rsi}\nStochastic: {stoch}"
    alert_type = "OVERSOLD"
    print("🚨 OVERSOLD condition met!")
elif rsi > 70 and stoch > 80:
    message = f"🚨 JUP OVERBOUGHT ALERT!\nPrice: ${price}\nRSI: {rsi}\nStochastic: {stoch}"
    alert_type = "OVERBOUGHT"
    print("🚨 OVERBOUGHT condition met!")
else:
    message = f"✅ JUP Status\nPrice: ${price}\nRSI: {rsi}\nStochastic: {stoch}"
    alert_type = "STATUS"
    print("✅ No alerts triggered")

# Send to Discord if webhook exists
if webhook:
    try:
        response = requests.post(webhook, json={"content": message}, timeout=5)
        if response.status_code == 204:
            print(f"✅ {alert_type} alert sent to Discord")
        else:
            print(f"❌ Discord error: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send to Discord: {e}")
else:
    print(f"📝 {alert_type} Message: {message}")

print("=== JUP TRADING BOT END ===")
print("✅ Bot execution completed successfully")
