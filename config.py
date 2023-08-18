# List of tickers. Leave empty to request all the updated tickers on binance.
# List with multiple intervals if desired: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
# Number of periods to analise
kline = dict(
    tickers=None,
    intervals=['15m', '30m', '1h', '4h'],
    n_periods=500,
    process_sleep=0.75,
)

# Telegram token of the Bot created with BotFather
# Telegram channel id
# Discord server webhook
live_bot = dict(
    telegram_token='6353435440:AAHnad4bweACrz8wYlFQ8Q2ohIT-xTmMpuI',
    telegram_chat_id=['-1001726074932', '-1001737404461']
)