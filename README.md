# Overview

This code contains two strategies implemented using the backtrader Python package, a library for backtesting trading strategies. The two strategies are:

### MACross: 

This is a simple moving average crossover strategy that buys when a shorter-term moving average crosses above a longer-term moving average and sells when the shorter-term moving average crosses below the longer-term moving average.

### MACD: 
This is a strategy based on the Moving Average Convergence Divergence (MACD) indicator, which uses a combination of two exponential moving averages to identify changes in momentum. This strategy enters the market when the MACD line crosses the signal line to the upside and the Simple Moving Average (SMA) has a negative direction in the last x periods. It sets a stop price x times the Average True Range (ATR) value away from the close, and updates the stop price if the new stop price would be higher than the current.

## Requirements
The code requires the following Python packages:

1. backtrader
2. pandas
3. datetime
4. logging

These packages can be installed using pip.

## Usage

To use the strategies, you can create an instance of either MACross or MACD and pass it to the backtrader Cerebro instance. The code also contains a runstrat function that takes a strategy instance, data feed, and cash amount as arguments and runs the strategy.

You can modify the parameters of the strategies by setting the values in the params dictionary of the respective strategy class. 

For example, to change the values of pfast and pslow in MACross, you would do:

    params = dict(
        pfast=5,
        pslow=10,
    )

    macross_strategy = MACross(**params)


## License

The code is released under the MIT license.

### To develop

1. Only long the market (buy only orders when there are no positions)
2. Only have spot orders (can't have margin)
3. How to adjust the risk? (AKA how much quantity to buy and sell, depending on the volume for the day)

### To enhance

1. Can we use ML to predict the orders to place the next day?
