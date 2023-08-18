# -*- coding: utf-8 -*-
"""
Created on Sat Apr  7 20:47:10 2018
@author: troymcfont
"""

# Imports
from telegram_helper import telegramBot
from binance.client import Client as BinanceClient
from binance.exceptions import BinanceAPIException
from nuats_ta import Candlestick, NuatsTA
import time
import config
from tqdm import *
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

# Get configuration from config.py
tickers = config.kline['tickers']
intervals = config.kline['intervals']
n_periods = config.kline['n_periods']
process_sleep = config.kline['process_sleep']

telegram_token = config.live_bot['telegram_token']
telegram_chat_ids = config.live_bot['telegram_chat_id']


class NotifyingThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    def __init__(self, max_workers=None):
        super().__init__(max_workers)

    def submit(self, fn, *args, **kwargs):
        # Create a wrapper function that includes a callback
        def wrapper_callback(future):
            global process_sleep
            # The callback function will be called when the task is done
            try:
                result = future.result()
                if len(result) > 0:
                    broadcast_signals(result)
                # Perform any additional notification or processing here
            except Exception as e:
                print(e)
        # Submit the task with the wrapper callback
        future = super().submit(fn, *args, **kwargs)
        future.add_done_callback(wrapper_callback)

        return future


# Functions
def request_tickers():
    tickeres = []
    bclient = BinanceClient().get_exchange_info()
    for element in bclient['symbols']:
        if element['status'] == 'TRADING' and element['quoteAsset'] == 'USDT' and 'USD' not in element['baseAsset']:
            tickeres.append(element['symbol'])
    return tickeres


def broadcast_signals(tickers_TA_list):
    # Filter out tickers with no bull/bear notifications
    all_notifications_list = list(filter(None.__ne__, tickers_TA_list))
    all_notifications_list.sort()
    for notification in all_notifications_list:
        print('Telegram broadcasting: \n {}'.format(telegram_chat_ids))
        # print('Discord broadcasting: \n {}'.format(discord_webhooks))
        telegramBot(token=telegram_token, chat_ids=telegram_chat_ids).broadcast_message(str(notification))


def TA_task(a):
    global process_sleep
    try:
        ticker, interval = a[0], a[1]
        print('Working on: {} Interval: {}'.format(ticker, interval))
        bclient = BinanceClient()

        klines = bclient.get_historical_klines(ticker, interval, n_periods)
        time.sleep(process_sleep)
        candles = []
        if len(klines) > 0:
            for kline in klines:
                candles.append(Candlestick(kline))
            nta = NuatsTA(ticker, interval, candles)
            return nta.analyse()

    except BinanceAPIException as e:
        print(e)
    except Exception as r:
        print(r)


def main():
    global tickers, intervals, n_periods, telegram_token, telegram_chat_ids

    # Get the tickers to analyse
    if tickers is None or not tickers:
        # This will request tickers from Binance.
        tickers = request_tickers()
    # Generate a list of tuples containing (ticker, interval)
    a = []
    for ticker in tickers:
        for interval in intervals:
            a.append((ticker, interval))

    # Loop over tickers and intervals to get signals (threading or serial)
    while True:
        with NotifyingThreadPoolExecutor(max_workers=4) as executor:
            future = list(tqdm(executor.submit(TA_task, i) for i in a))
            concurrent.futures.wait(future)


if __name__ == '__main__':
    main()
