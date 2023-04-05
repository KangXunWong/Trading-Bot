from datetime import datetime as dt, timedelta
import backtrader as bt
import pandas_datareader.data as web
from pandas_datareader.yahoo.headers import DEFAULT_HEADERS
import requests_cache


def backtest_pandas_datareader(model):
    # Create a backtest instance
    cerebro = bt.Cerebro()
    # Set the initial cash
    cerebro.broker.set_cash(10000)
    # Load data

    # start & end date
    end_date = dt.today()
    start_date = end_date - timedelta(days = 365 )

    # configure session timeout
    expire_after = timedelta(days=3)
    session = requests_cache.CachedSession(cache_name='cache', backend='sqlite', expire_after=expire_after)
    session.headers = DEFAULT_HEADERS

    data = web.DataReader('^DJI', 'stooq', start = start_date, end = end_date, session = session).reset_index()

    # create a data feed from the Pandas DataFrame
    data_feed = bt.feeds.PandasData(dataname=data, datetime='Date')

    # Add data and strategy to the instance
    cerebro.adddata(data_feed)
    cerebro.addstrategy(model)
    # cerebro.addstrategy(MACD)
    # Run the backtest
    cerebro.run()
    # cerebro.plot()
    # Print the final portfolio value
    print(f'Final portfolio value: {cerebro.broker.getvalue()}')
