from datetime import datetime, timedelta

# Backtesting parameters
BACKTEST_CONFIG = {
    'symbol': 'NIFTY50',
    'intervals': ['5min', '10min', '15min'],
    'lookback_days': 30,  # Number of days of historical data to use
    'initial_capital': 100000,  # Initial capital in INR
    'position_size': 0.95,  # Position size as fraction of capital (increased to allow NIFTY trades)
    'max_positions': 1,  # Maximum number of concurrent positions
    'slippage': 0.001,  # Slippage per trade (0.1%)
    'commission': 0.0003,  # Commission per trade (0.03%)
    'report_dir': 'reports',  # Directory for saving reports
    'results_dir': 'results',  # Directory for saving results
}

# Strategy parameters
STRATEGY_CONFIG = {
    'rsi': {
        'period': 14,
        'overbought': 70.0,  # Increased from 60.0
        'oversold': 30.0,    # Decreased from 40.0
        'use_crossover': True
    },
    'supertrend': {
        'atr_period': 10,
        'atr_multiplier': 1.5  # Reduced from 2.0
    },
    'ema': {
        'period': 200,
        'use_ema_filter': False  # Disabled EMA filter initially
    },
    'risk_management': {
        'stop_loss_atr_multiplier': 1.5,
        'take_profit_atr_multiplier': 2.0,
        'trailing_stop': True,
        'trailing_stop_atr_multiplier': 1.0
    },
    'trade_filters': {
        'min_atr_threshold': 0.001,  # Reduced from 0.002
        'skip_lunch_hours': False,   # Disabled lunch hour filter
        'lunch_start': '12:00',
        'lunch_end': '13:30'
    }
}

def get_date_range():
    """Get the date range for backtesting."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=BACKTEST_CONFIG['lookback_days'])
    return start_date, end_date 