import ccxt
import pandas as pd
import time
from datetime import datetime

def calculate_cvd(symbol="BTC/USDT", limit=1000):
    """
    Calculates Cumulative Volume Delta (CVD) for a given symbol on Bybit using public trades.
    """
    print(f"--- Calculating CVD for {symbol} ---")
    
    # Initialize Bybit client (public data doesn't require API keys)
    exchange = ccxt.bybit()
    
    try:
        # Fetch recent trades
        # Note: standard fetch_trades gets the latest trades. 
        # For a longer history, you'd need pagination, but this is a snapshot example.
        print(f"Fetching last {limit} trades...")
        trades = exchange.fetch_trades(symbol, limit=limit)
        
        if not trades:
            print("No trades found.")
            return

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(trades)
        
        # Ensure 'side' and 'amount' are present and correct types
        df['amount'] = df['amount'].astype(float)
        df['price'] = df['price'].astype(float)
        
        # Calculate Delta for each trade
        # Buy = +Volume, Sell = -Volume
        df['delta'] = df.apply(lambda x: x['amount'] if x['side'] == 'buy' else -x['amount'], axis=1)
        
        # Calculate Cumulative Delta
        df['cvd'] = df['delta'].cumsum()
        
        # Basic Stats
        total_volume = df['amount'].sum()
        buy_volume = df[df['side'] == 'buy']['amount'].sum()
        sell_volume = df[df['side'] == 'sell']['amount'].sum()
        total_delta = df['delta'].sum()
        
        print(f"\nAnalysis of last {len(df)} trades:")
        print(f"Start Time: {df['datetime'].iloc[0]}")
        print(f"End Time:   {df['datetime'].iloc[-1]}")
        print(f"Total Volume: {total_volume:.4f}")
        print(f"Buy Volume:   {buy_volume:.4f}")
        print(f"Sell Volume:  {sell_volume:.4f}")
        print(f"Final CVD:    {total_delta:.4f}")
        
        # Detect Divergence (Simple comparison of Price vs CVD trend)
        first_price = df['price'].iloc[0]
        last_price = df['price'].iloc[-1]
        price_change = (last_price - first_price) / first_price * 100
        
        first_cvd = df['cvd'].iloc[0] # Likely close to 0 or delta of first trade
        last_cvd = df['cvd'].iloc[-1]
        cvd_change = last_cvd - first_cvd # Should match total_delta if starting from 0
        
        print(f"\nPrice Change: {price_change:.4f}%")
        print(f"CVD Change:   {cvd_change:.4f}")
        
        if price_change < 0 and cvd_change > 0:
            print("\n⚠️ DIVERGENCE DETECTED: Price Down, CVD Up (Bullish Absorption)")
        elif price_change > 0 and cvd_change < 0:
            print("\n⚠️ DIVERGENCE DETECTED: Price Up, CVD Down (Bearish Absorption)")
        else:
            print("\nConvergence: Price and CVD moving together.")

        return df

    except Exception as e:
        print(f"Error: {e}")
    finally:
        exchange.close()

if __name__ == "__main__":
    calculate_cvd("BTC/USDT", limit=1000)

