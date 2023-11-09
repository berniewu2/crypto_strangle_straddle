import pandas as pd
import ccxt
import time
import datetime

def backtest_strategy(exchange, start_date, end_date, lower_volatility, higher_volatility):
    def calculate_implied_volatility(c):
        premium = (c['bidPrice'] + c['askPrice']) / 2
        underlying_price = c['underlyingPrice']
        strike_price = c['strikePrice']
        time_to_expiration = (c['expiration'] - int(time.time())) / (60 * 60 * 24)
        volatility = premium / (underlying_price * strike_price * time_to_expiration ** 0.5)
        return volatility

    def calculate_total_pnl(option_trades):
        pnl = 0
        for trade in option_trades:
            pnl += trade['pnl']
        return pnl

    def calculate_max_drawdown(option_trades):
        max_drawdown = 0
        equity = 0
        for trade in option_trades:
            equity += trade['pnl']
            max_drawdown = max(max_drawdown, equity)
        return max_drawdown

    timeframe = '1d'
    ohlcv_df = pd.DataFrame()

    since = int(time.mktime(datetime.datetime.strptime(start_date, '%Y-%m-%d').timetuple()))
    limit = 2000

    while True:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe, since, limit)
        ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        print(ohlcv)
        print(ohlcv_df)
        ohlcv_df['timestamp'] = pd.to_datetime(ohlcv_df['timestamp'], unit='ms')

        if ohlcv_df.iloc[-1]['timestamp'].date() >= datetime.datetime.strptime(end_date, '%Y-%m-%d').date():
            break

        time.sleep(exchange.rateLimit / 1000)
        since = ohlcv_df.iloc[-1]['timestamp'].value / 1000000 + 1

    ohlcv_df = ohlcv_df.set_index('timestamp')

    options_df = pd.DataFrame()

    while True:
        options = exchange.fetch_option_markets()
        for option in options:
            if option['quote'] == 'USDT':
                options_df = options_df.append(option)

        if options_df.empty:
            time.sleep(exchange.rateLimit / 1000)
        else:
            break

    option_trades = []

    for index, row in options_df.iterrows():
        try:
            oi = exchange.fetch_option_open_interest(row['id'])
            option_market_depth = exchange.fetch_option_order_book(row['id'])

            bid = option_market_depth['bids'][0]
            ask = option_market_depth['asks'][0]

            current_time = int(time.time())
            days_to_expiration = (row['expiration'] - current_time) / (60 * 60 * 24)

            volatility = calculate_implied_volatility(oi)

            if volatility < lower_volatility:
                # Short Straddle
                strike_price = row['strikePrice']
                premium = (bid['price'] + ask['price']) / 2
                entry_price = (strike_price * premium) / 2
                pnl = entry_price - strike_price
                option_trades.append({'timestamp': pd.to_datetime(current_time, unit='s'), 'pnl': pnl})
            elif volatility > higher_volatility:
                # Long Straddle
                strike_price = row['strikePrice']
                premium = (bid['price'] + ask['price']) / 2
                entry_price = (strike_price * premium) / 2
                pnl = strike_price - entry_price
                option_trades.append({'timestamp': pd.to_datetime(current_time, unit='s'), 'pnl': pnl})

            time.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"Error processing option {row['id']}: {str(e)}")
            time.sleep(exchange.rateLimit / 1000)

    total_pnl = calculate_total_pnl(option_trades)
    max_drawdown = calculate_max_drawdown(option_trades)

    print(f"Total Trades: {len(option_trades)}")

    print(f"Total PNL: {total_pnl}")
    print(f"Max Drawdown: {max_drawdown}")

backtest_strategy(ccxt.kucoin(), '2021-01-01', '2021-01-31', 0.5, 1.5)

