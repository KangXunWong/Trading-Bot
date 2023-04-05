from datetime import datetime as dt, timedelta
import logging
import pandas as pd
import backtrader as bt
import pandas_datareader.data as web
from pandas_datareader.stooq import StooqDailyReader
from pandas_datareader.yahoo.headers import DEFAULT_HEADERS
from dateutil.relativedelta import relativedelta
import requests_cache
import models as m

if __name__ == '__main__':

    # Create a backtest instance
    cerebro = bt.Cerebro(stdstats = False, cheat_on_open=True)

    cerebro.addstrategy(m.MACD)

    #cerebro.addsizer(bt.sizers.SizerFix, stake=20)
    
    # Set the initial cash and broker commission 
    initial_amount = 10000
    cerebro.broker.set_cash(initial_amount)
    cerebro.broker.setcommission(commission=0.001)

    # Set an oberver and analyser
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.Value)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')

    # Create logging instance
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging_handler = logging.FileHandler("backtrader.log")
    logger.addHandler(logging_handler)
    formatted_date = dt.today().strftime("%Y_%m_%d_T%H_%M_%S")
    # cerebro.addwriter(bt.WriterFile, out = f"CSV/backtested_trades_{formatted_date}.csv", csv=True)

    # start & end date
    end_date = dt.today()
    #start_date = end_date - timedelta(days = 365 )
    start_date = end_date - relativedelta (years =1) 

    # # configure session timeout
    # expire_after = timedelta(days=31)
    # session = requests_cache.CachedSession(cache_name='cache', backend='sqlite', expire_after=expire_after)
    # session.headers = DEFAULT_HEADERS

    # data = web.DataReader('^SPX', 'stooq', start = start_date, end = end_date)
    data=StooqDailyReader("MSTR.US").read()
    data = data.sort_values(by='Date', ascending=True).reset_index()
    # create a data feed from the Pandas DataFrame
    data_feed = bt.feeds.PandasData(dataname=data, datetime='Date')     
    
    # Load data
    cerebro.adddata(data_feed)

    # Run the backtest
    cerebro.run()
    # cerebro.plot()
    # Print the final portfolio value
    final_amount = cerebro.broker.getvalue() 
    print(f'Final portfolio value: {final_amount}')
    percentage_change = (final_amount - initial_amount)/initial_amount * 100.0
    print(f'Percentage Gain / (Loss): {percentage_change}%')

    # Print the final portfolio value for each strategy
    # Add data strategy to the instance
    # strategies = [MACross,MACD,EMAStrategy,RSI_SMA_Strategy] 
    # for strategy in strategies:
    #     cerebro.addstrategy(strategy)
    #     final_amount = cerebro.broker.getvalue() 
    #     percentage_change = (final_amount - initial_amount)/initial_amount * 100.0 
    #     print(f"{strategy.__class__.__name__}: {cerebro.broker.getvalue():,.2f} / {percentage_change:,.2f}")