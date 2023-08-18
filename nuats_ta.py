# https://github.com/rpazyaquian/PyTA

import pandas
import numpy as np
import ta.momentum as tam
import ta.trend as tat
import ta.volatility as tav


class Candlestick(object):

    def __init__(self, kline):
        self.open_time = kline[0]
        self.open = float(kline[1])
        self.high = float(kline[2])
        self.low = float(kline[3])
        self.close = float(kline[4])
        self.volume = float(kline[5])
        self.close_time = kline[6]

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class Notification(object):
    """
    Types:
        0: RSI bull
        1: RSI bear
        2: Volume increase
        3: RSI-price bull divergence
        4: RSI-price bear divergence
    """

    def __init__(self, code, ticker, interval, rsi, stochk, stochd, macd, atr, entry_price):
        self.code = code
        self.ticker = ticker
        self.interval = interval
        self.rsi = rsi
        self.stochk = stochk
        self.stochd = stochd
        self.atr = atr
        self.macd = macd
        self.entry_price = entry_price

    def __str__(self):
        if self.code == 0:
            return f"""
(🔴🔴SELL/SHORT🔴🔴)

Platform: BINANCE

Pair: {self.ticker}

Interval: {self.interval}

Entry Price: {'{:,.15f}'.format(self.entry_price)}

Stop Lose: {'{:,.15f}'.format(self.entry_price + (self.atr * 2))}

Indicators Analysis
RSI: {'{:,.1f}'.format(self.rsi)}
StochRSI K: {'{:,.1f}'.format(self.stochk)}
StochRSI D: {'{:,.1f}'.format(self.stochd)}
MACD: {'{:,.5f}'.format(self.macd)}
"""
        elif self.code == 1:
            return f"""
(🟢🟢BUY/LONG🟢🟢)

Platform: BINANCE

Pair: {self.ticker}

Interval: {self.interval}

Entry Price: {'{:,.15f}'.format(self.entry_price)}

Stop Lose: {'{:,.15f}'.format(self.entry_price - (self.atr * 2))}

Indicators Analysis
RSI: {'{:,.1f}'.format(self.rsi)}
StochRSI K: {'{:,.1f}'.format(self.stochk)}
StochRSI D: {'{:,.1f}'.format(self.stochd)}
MACD: {'{:,.5f}'.format(self.macd)}
"""
        else:
            return 'Error (no code present)'

    def __lt__(self, other):
        return self.ticker < other.ticker


class NuatsTA(object):

    def __init__(self, ticker, interval, candles):
        self.ticker = ticker
        self.interval = interval
        self.candles = candles
        self.prices = pandas.Series(np.asarray([candle.close for candle in candles]))
        self.prices_highs = pandas.Series(np.asarray([candle.high for candle in candles]))
        self.prices_lows = pandas.Series(np.asarray([candle.low for candle in candles]))
        self.n_periods = len(candles)
        self.indicators = {}

    def analyse(self):
        notifications = []
        try:
            # Compute indicators
            rsi, fastk, fastd = self.StochRsi()
            MACD, macdsignal = self.MACD()
            ATR = self.ATR()
            entry_price = self.prices.iloc[-1]
            # chart_path = self.chart(rsi, MACD, macdsignal)
            if ((
                    fastd.iloc[-1] < 20
                    and fastk.iloc[-1] < 20
                    and MACD.iloc[-1] > macdsignal.iloc[-1]
                    and MACD.iloc[-2] < macdsignal.iloc[-2]
            ) or (
                    fastd.iloc[-1] < 20
                    and fastk.iloc[-1] < 20
                    and MACD.iloc[-1] > macdsignal.iloc[-1]
                    and MACD.iloc[-3] < macdsignal.iloc[-3]
                    and fastd.iloc[-1] < 80
                    and fastk.iloc[-1] < 80
            )):
                notifications.append(
                    Notification(
                        code=1,
                        ticker=self.ticker,
                        interval=self.interval,
                        rsi=rsi.iloc[-1],
                        stochk=fastk.iloc[-1],
                        stochd=fastd.iloc[-1],
                        macd=MACD.iloc[-1],
                        atr=ATR.iloc[-1],
                        entry_price=entry_price
                    )
                )
            elif ((
                    fastd.iloc[-1] > 80
                    and fastk.iloc[-1] > 80
                    and MACD.iloc[-1] < macdsignal.iloc[-1]
                    and MACD.iloc[-2] > macdsignal.iloc[-2]
            ) or (
                    fastd.iloc[-2] > 80
                    and fastk.iloc[-2] > 80
                    and MACD.iloc[-1] < macdsignal.iloc[-1]
                    and MACD.iloc[-3] > macdsignal.iloc[-3]
                    and fastd.iloc[-1] > 20
                    and fastk.iloc[-1] > 20
            )):
                notifications.append(
                    Notification(
                        code=0,
                        ticker=self.ticker,
                        interval=self.interval,
                        rsi=rsi.iloc[-1],
                        stochk=fastk.iloc[-1],
                        stochd=fastd.iloc[-1],
                        macd=MACD.iloc[-1],
                        atr=ATR.iloc[-1],
                        entry_price=entry_price
                    )
                )

            return notifications
        except Exception as e:
            print(e)

    def StochRsi(self):
        """
        Returns the Relative Strength Index for a list of stock prices "prices"
        over a period of time "timeframe".
        Code shamelessly stolen from Sentdex. Sorry!

        Accepts: Array; integer (optional).
        Return type: Array.
        """
        # Calculate RSI
        rsi = tam.rsi(close=self.prices)

        # Calculate Stochastic RSI
        stochrsi_k = tam.stoch_signal(close=self.prices, high=self.prices_highs, low=self.prices_lows)
        stochrsi_d = tam.stoch(close=self.prices, high=self.prices_highs, low=self.prices_lows)
        # stochrsi_k = tam.stochrsi_k(close=self.prices)
        # stochrsi_d = tam.stochrsi_d(close=self.prices)

        # Convert RSI and Stochastic RSI to pandas Series for easy visualization
        rsi = pandas.Series(rsi, name='RSI')
        stochrsi_k = pandas.Series(stochrsi_k, name='StochRSI_K')
        stochrsi_d = pandas.Series(stochrsi_d, name='StochRSI_D')
        return rsi, stochrsi_k, stochrsi_d  # Returns a Numpy Array.

    def MACD(self):
        """
        Returns the Moving Average Convergence-Divergence (MACD) of a given set of price data.
        This is the main line for plotting on a chart.

        Accepts: Array.
        Return type: Array.
        """

        # Calculate MACD
        macd = tat.macd(close=self.prices)
        macd_signal = tat.macd_signal(close=self.prices)
        # Convert MACD and signal to pandas Series for easy visualization
        macd = pandas.Series(macd, name='MACD')
        macd_signal = pandas.Series(macd_signal, name='MACD_Signal')
        return macd, macd_signal

    def ATR(self):
        """
        return the ATR of the dataframe for the given dataframe name and data

        Accepts: Array.
        Return type: Array.
        """
        # Calculate ATR with a period of 14 (can be adjusted based on your preference)
        ATR = tav.average_true_range(high=self.prices_highs, low=self.prices_lows, close=self.prices)

        # Convert ATR to a pandas Series for easy visualization
        atr = pandas.Series(ATR, name='ATR')
        return atr

    # def chart(self, rsi, macd, macd_signal):
    #     # Create a chart with prices, RSI, and MACD
    #     plt.figure(figsize=(12, 8))
    #     plt.subplot(3, 1, 1)
    #     plt.plot(self.prices, label='Price')
    #     plt.legend()
    #     plt.title('Price Chart')
    #     plt.grid(True)
    #
    #     plt.subplot(3, 1, 2)
    #     plt.plot(rsi, label='RSI')
    #     plt.axhline(70, color='r', linestyle='--')
    #     plt.axhline(30, color='r', linestyle='--')
    #     plt.legend()
    #     plt.title('RSI Chart')
    #     plt.grid(True)
    #
    #     plt.subplot(3, 1, 3)
    #     plt.plot(macd, label='MACD')
    #     plt.plot(macd_signal, label='MACD Signal')
    #     plt.legend()
    #     plt.title('MACD Chart')
    #     plt.grid(True)
    #
    #     plt.tight_layout()
    #
    #     # Save the chart as an image file
    #     image_path = f'{self.ticker}.png'
    #     plt.savefig(image_path)
    #     plt.close()
    #     return image_path
