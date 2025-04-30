import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.supertrend_rsi import SupertrendRsiStrategy
from .engine import BacktestEngine
from .config import BACKTEST_CONFIG, STRATEGY_CONFIG, get_date_range

def generate_sample_data(n=1000, start_date=None, interval='15min'):
    """Generate sample OHLCV data for testing."""
    if start_date is None:
        start_date = pd.Timestamp('2023-01-01')
    
    # Convert interval to minutes
    interval_minutes = int(interval.replace('min', ''))
    
    # Generate timestamps for market hours (9:15 AM to 3:30 PM)
    dates = []
    current_date = start_date
    while len(dates) < n:
        if current_date.weekday() < 5:  # Monday to Friday
            for hour in range(9, 15):
                for minute in [15, 30, 45] if hour == 9 else range(0, 60, interval_minutes):
                    if hour == 15 and minute > 30:
                        continue
                    dates.append(current_date.replace(hour=hour, minute=minute))
        current_date += pd.Timedelta(days=1)
    dates = dates[:n]
    
    # Generate realistic price movements
    initial_price = 17500  # Starting price for NIFTY
    daily_volatility = 0.02  # 2% daily volatility
    
    # Generate returns with slight upward bias and scaled volatility for the given interval
    intervals_per_day = 375 // interval_minutes  # 375 minutes in a trading day
    interval_volatility = daily_volatility / np.sqrt(intervals_per_day)
    returns = np.random.normal(0.0005, interval_volatility, n)  # Increased mean return
    
    # Add some momentum effect
    momentum = np.zeros(n)
    for i in range(1, n):
        momentum[i] = momentum[i-1] * 0.7 + returns[i-1] * 0.3
    
    # Combine returns with momentum
    final_returns = returns + momentum * 0.5
    
    # Calculate prices using cumulative returns
    closes = initial_price * np.exp(np.cumsum(final_returns))
    
    # Generate OHLC data with realistic spreads
    spreads = np.random.uniform(0.3, 0.6, n) * closes  # Increased spreads (0.3% to 0.6%)
    opens = closes * (1 + np.random.uniform(-0.003, 0.003, n))  # Wider open range
    highs = np.maximum(opens, closes) + spreads/2
    lows = np.minimum(opens, closes) - spreads/2
    
    # Generate volume with some randomness and correlation to price moves
    base_volume = np.random.uniform(200000, 500000, n)  # Increased base volume
    volume = base_volume * (1 + 3 * np.abs(final_returns))  # Higher volume on larger price moves
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volume.astype(int)
    })
    
    df.set_index('timestamp', inplace=True)
    return df

def main():
    """Run backtest for different intervals."""
    # Initialize strategy with all parameters
    strategy = SupertrendRsiStrategy(
        rsi_period=STRATEGY_CONFIG['rsi']['period'],
        rsi_overbought=STRATEGY_CONFIG['rsi']['overbought'],
        rsi_oversold=STRATEGY_CONFIG['rsi']['oversold'],
        rsi_crossover=STRATEGY_CONFIG['rsi']['use_crossover'],
        supertrend_atr_period=STRATEGY_CONFIG['supertrend']['atr_period'],
        supertrend_atr_multiplier=STRATEGY_CONFIG['supertrend']['atr_multiplier'],
        ema_period=STRATEGY_CONFIG['ema']['period'],
        ema_use_filter=STRATEGY_CONFIG['ema']['use_ema_filter'],
        risk_management_stop_loss_atr_multiplier=STRATEGY_CONFIG['risk_management']['stop_loss_atr_multiplier'],
        risk_management_take_profit_atr_multiplier=STRATEGY_CONFIG['risk_management']['take_profit_atr_multiplier'],
        risk_management_trailing_stop=STRATEGY_CONFIG['risk_management']['trailing_stop'],
        risk_management_trailing_stop_atr_multiplier=STRATEGY_CONFIG['risk_management']['trailing_stop_atr_multiplier'],
        trade_filters_min_atr_threshold=STRATEGY_CONFIG['trade_filters']['min_atr_threshold'],
        trade_filters_skip_lunch_hours=STRATEGY_CONFIG['trade_filters']['skip_lunch_hours'],
        trade_filters_lunch_start=datetime.strptime(STRATEGY_CONFIG['trade_filters']['lunch_start'], '%H:%M').time(),
        trade_filters_lunch_end=datetime.strptime(STRATEGY_CONFIG['trade_filters']['lunch_end'], '%H:%M').time()
    )
    
    # Initialize backtest engine
    engine = BacktestEngine(strategy=strategy)
    
    # Run backtest for each interval
    for interval in BACKTEST_CONFIG['intervals']:
        print(f"\nRunning backtest for {interval} interval...")
        data = generate_sample_data(interval=interval)
        results = engine.run_backtest(data)
        
        # Print results
        print(f"Total Trades: {results['total_trades']}")
        print(f"Winning Trades: {results['winning_trades']}")
        print(f"Losing Trades: {results['losing_trades']}")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"Total Profit/Loss: ₹{results['total_profit_loss']:.2f}")
        print(f"Average Profit per Trade: ₹{results['avg_profit_per_trade']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")

if __name__ == "__main__":
    main() 