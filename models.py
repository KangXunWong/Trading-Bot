from datetime import datetime as dt, timedelta
import logging
import pandas as pd
import backtrader as bt
import pandas_datareader.data as web
from pandas_datareader.yahoo.headers import DEFAULT_HEADERS
from dateutil.relativedelta import relativedelta
import requests_cache


class MACross(bt.Strategy):
    params = (
        ('pfast', 1),
        ('pslow', 5),
    )

    def __init__(self):

        # instantiate moving averages
        self.sma_short = bt.indicators.SMA(self.data, period=self.params.pfast)
        self.sma_long = bt.indicators.SMA(self.data, period=self.params.pslow)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)

        # Order variable will contain ongoing order details/status
        self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logging.info(f'{dt.isoformat()} {txt}') # Comment this line when running optimization

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # order already submitted/accepted - no action required
            return
		# Check if an order has been completed
		# Attention: broker could reject order if not enough cash
        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    f'SELL EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )

        # report failed order
        elif order.status in [order.Canceled, order.Margin, 
                              order.Rejected]:
            self.log('Order Failed')

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION RESULT --- Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')

    def next(self):
		# Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # We are not in the market, look for a signal to OPEN trades
                
            #If the 20 SMA is above the 50 SMA
            if self.sma_short[0] > self.sma_long[0] and self.sma_short[-1] < self.sma_long[-1]:
                self.log(f'------------------BUY CREATE: {self.data[0]}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(exectype=bt.Order.Market,price=self.data.close[0])
            #Otherwise if the 20 SMA is below the 50 SMA   
            elif self.sma_short[0] < self.sma_long[0] and self.sma_short[-1] > self.sma_long[-1]:
                self.log(f'------------------SELL CREATE: {self.data[0]}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(exectype=bt.Order.Market,price=self.data.close[0])
        else:
            # We are already in the market, look for a signal to CLOSE trades
            if len(self) >= (self.bar_executed + 5):
                self.log(f'------------------CLOSE CREATE: {self.data[0]}')
                self.order = self.close()


class MACD(bt.Strategy):
    '''
    This strategy is loosely based on some of the examples from the Van
    K. Tharp book: *Trade Your Way To Financial Freedom*. The logic:

      - Enter the market if:
        - The MACD.macd line crosses the MACD.signal line to the upside
        - The Simple Moving Average has a negative direction in the last x
          periods (actual value below value x periods ago)

     - Set a stop price x times the ATR value away from the close

     - If in the market:

       - Check if the current close has gone below the stop price. If yes,
         exit.
       - If not, update the stop price if the new stop price would be higher
         than the current
    '''

    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9), # Above 3 parameters are to create the MACD
        ('atrperiod', 14),  # ATR Period (standard)
        ('atrdist', 3.0),   # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data,
            period_me1=self.params.macd1, 
            period_me2=self.params.macd2, 
            period_signal=self.params.macdsig)
        
        # Cross of macd.macd and macd.signal
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        # To set the stop price
        self.atr = bt.indicators.ATR(self.data, period=self.params.atrperiod)

        # Control market trend
        self.sma = bt.indicators.SMA(self.data, period=self.params.smaperiod)
        self.smadir = self.sma - self.sma(-self.params.dirperiod)
        
        self.order = None  # sentinel to avoid operations on pending order

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logging.info(f'{dt.isoformat()} {txt}') # Comment this line when running optimization

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # order already submitted/accepted - no action required
            return
		# Check if an order has been completed
		# Attention: broker could reject order if not enough cash
        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    f'SELL EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )

        # report failed order
        elif order.status in [order.Canceled, order.Margin, 
                              order.Rejected]:
            self.log('Order Failed')

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION RESULT --- Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')

    def next(self):

        if self.order:
            return  # pending order execution, there is an order open
        
        if not self.position:  # not in the market
            if self.mcross[0] > 0.0 and self.smadir < 0.0:
                self.order = self.buy()
                pdist = self.atr[0] * self.params.atrdist
                pstop = self.data.close[0] - pdist

        else:  # in the market
            pclose = self.data.close[0]
            pstop = self.data.close[0] - pdist

            if pclose < pstop:
                self.close()  # stop met - get out of the existing position
            else:
                pdist = self.atr[0] * self.params.atrdist
                # Update only if greater than
                pstop = max(pstop, pclose - pdist)

'''
        if not self.position and self.macd1.lines.macd[0] > self.macd1.lines.signal[0]:
            self.buy()
        elif self.position and self.macd1.lines.macd[0] < self.macd1.lines.signal[0]:
            self.sell()
'''

class EMAStrategy(bt.Strategy):
    params = (
        ('ema_period', 50),
        ('sma_period', 200),
    )
    
    def __init__(self):
        self.ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.ema_period)
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.sma_period)

        self.order = None # Initiate an order to create none

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logging.info(f'{dt.isoformat()} {txt}') # Comment this line when running optimization

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # order already submitted/accepted - no action required
            return

        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    f'SELL EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )

        # report failed order
        elif order.status in [order.Canceled, order.Margin, 
                              order.Rejected]:
            self.log('Order Failed')

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION RESULT --- Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')

    def next(self):

        if not self.position:
            if self.ema > self.sma:
                self.buy()
        elif self.ema < self.sma:
            self.close()

class RSI_SMA_Strategy(bt.Strategy):
    params = dict(rsi_periods=21, rsi_upper=70, 
                  rsi_lower=30, rsi_mid=50,
                 sma_periods=14, sma_periods2=50)

    def __init__(self):
        # keep track of close price in the series
        self.data_close = self.datas[0].close
        self.data_open = self.datas[0].open

        # keep track of pending orders/buy price/buy commission
        self.order = None
        self.price = None
        self.comm = None

        # initializing rsi and sma
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.p.rsi_periods)
        
        self.sma14=bt.ind.SMA(self.datas[0], period=self.params.sma_periods)
        self.sma50=bt.ind.SMA(self.datas[0], period=self.params.sma_periods2)
        
        self.rsi_signal_long_buy = bt.ind.CrossUp(self.rsi, self.p.rsi_lower)
        self.rsi_signal_long_exit = bt.ind.CrossUp(self.rsi, self.p.rsi_mid)
        self.rsi_signal_short = bt.ind.CrossDown(self.rsi, self.p.rsi_upper)

    def log(self, txt):
        '''Logging function'''
        dt = self.datas[0].datetime.date(0)
        logging.info(f'{dt.isoformat()} {txt}') # Comment this line when running optimization
        # print(f'{dt}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # order already submitted/accepted - no action required
            return

        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    f'SELL EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Commission: {order.executed.comm:.2f}'
                )

        # report failed order
        elif order.status in [order.Canceled, order.Margin, 
                              order.Rejected]:
            self.log('Order Failed')

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION RESULT --- Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')

    def next_open(self):
        if not self.position:
            if self.rsi > 30 and self.sma14 > self.sma50:
                # calculate the max number of shares ('all-in')
                size = int(self.broker.getcash() / self.datas[0].open)
                # buy condition
                self.log(f'BUY CREATED --- Size: {size}, Cash: {self.broker.getcash():.2f}, Open: {self.data_open[0]}, Close: {self.data_close[0]}')
                self.order = self.buy(size=size)
        else:
            if self.rsi < 70 and self.sma14 < self.sma50:
                # sell order
                self.log(f'SELL CREATED --- Size: {self.position.size}')
                self.order = self.sell(size=self.position.size)