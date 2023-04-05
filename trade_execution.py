import pandas as pd
import numpy as np
import talib
import time
import ccxt

# Set up API credentials for your preferred exchange
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY'
})

# Define the parameters for MACD, RSI, and ADX indicators
macd_fast = 12
macd_slow = 26
macd_signal = 9
rsi_period = 14
adx_period = 14
adx_threshold = 25

# Define the symbol you want to trade and the timeframe for the candlestick data
symbol = 'BTC/USDT'
timeframe = '1h'

# Define the trade value in USDT
trade_value = 1000

# Define the number of candles to use for confirmation
confirmation_candles = 48 # 2 days for 1h timeframe

# Set up an initial value for position
position = None

# Set up an infinite loop to keep the bot running
while True:

    # Fetch the candlestick data from the exchange
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Calculate the MACD, RSI, and ADX indicators
    macd, signal, hist = talib.MACD(df['close'], fastperiod=macd_fast, slowperiod=macd_slow, signalperiod=macd_signal)
    rsi = talib.RSI(df['close'], timeperiod=rsi_period)
    adx = talib.ADX(df['high'], df['low'], df['close'], timeperiod=adx_period)
    
    # Check if there is a bullish MACD crossover
    if macd[-2] < signal[-2] and macd[-1] > signal[-1]:
        
        # Confirm the signal by checking if the MACD stays above the signal line for confirmation_candles
        if np.all(macd[-confirmation_candles:] > signal[-confirmation_candles:]):
            
            # Confirm the signal by checking if the RSI is above 50 and the ADX is above the threshold
            if rsi[-1] > 50 and adx[-1] > adx_threshold:

                # Close a short position, if any
                if position == 'short':
                    order = exchange.create_market_buy_order(symbol, amount_short)
                    print('Buy order executed at', order['price'], 'on', pd.to_datetime(order['timestamp'], unit='ms'))
                    position = None
                
                # Enter a long position, if no position is open
                if not position:
                    # Calculate the amount to buy based on the trade value and the current price
                    price = exchange.fetch_ticker(symbol)['bid']
                    amount_long = trade_value / price

                    order = exchange.create_market_buy_order(symbol, amount_long)
                    print('Buy order executed at', order['price'], 'on', pd.to_datetime(order['timestamp'], unit='ms'))
                    position = 'long'
                
                # Wait for 2 days before placing another order
                time.sleep(172800) # 2 days = 2 * 24 * 60 * 60 seconds
    
    # Check if there is a bearish MACD crossover
    elif macd[-2] > signal[-2] and macd[-1] < signal[-1]:
        
        # Confirm the signal by checking if the MACD stays below the signal line for confirmation_candles
        if np.all(macd[-confirmation_candles:] < signal[-confirmation_candles:]):
            
            # Confirm the signal by checking if the RSI is below 50 and the ADX is above the threshold
            if rsi[-1] < 50 and adx[-1] > adx_threshold:

                # Close a short position, if any
                if position == 'long':
                    order = exchange.create_market_buy_order(symbol, amount_long)
                    print('Buy order executed at', order['price'], 'on', pd.to_datetime(order['timestamp'], unit='ms'))
                    position = None

                # Enter a long position, if no position is open
                if not position:

                    # Calculate the amount to buy based on the trade value and the current price
                    price = exchange.fetch_ticker(symbol)['bid']
                    amount_short = trade_value / price

                    # Enter a short position
                    order = exchange.create_market_sell_order(symbol, amount_short)
                    print('Sell order executed at', order['price'], 'on', pd.to_datetime)
                    position = 'short'

                # Wait for 2 days before placing another order
                time.sleep(172800) # 2 days = 2 * 24 * 60 * 60 seconds
                
