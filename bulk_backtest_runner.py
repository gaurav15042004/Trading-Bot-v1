import itertools
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any
from backtest.engine import BacktestEngine
from strategies.supertrend_rsi import SupertrendRsiStrategy
from backtest.run_backtest import generate_sample_data
from backtest.config import BACKTEST_CONFIG
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_param_combinations(grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """
    Generate all possible combinations of parameters from the grid.
    
    Args:
        grid: Dictionary of parameter names and their possible values
        
    Returns:
        List of dictionaries containing parameter combinations
    """
    keys = grid.keys()
    values = grid.values()
    combinations = []
    
    for combination in itertools.product(*values):
        param_dict = dict(zip(keys, combination))
        combinations.append(param_dict)
    
    return combinations

def run_backtest(params):
    """Run a single backtest with the given parameters."""
    try:
        # Create a copy of the parameters to avoid modifying the original
        strategy_params = {}
        
        # Map flattened parameters to nested structure
        param_mapping = {
            'rsi_period': 'rsi_period',
            'rsi_overbought': 'rsi_overbought',
            'rsi_oversold': 'rsi_oversold',
            'rsi_crossover': 'rsi_crossover',
            'atr_period': 'supertrend_atr_period',
            'atr_multiplier': 'supertrend_atr_multiplier',
            'ema_period': 'ema_period',
            'use_ema_filter': 'ema_use_filter',
            'stop_loss_atr_multiplier': 'risk_management_stop_loss_atr_multiplier',
            'take_profit_atr_multiplier': 'risk_management_take_profit_atr_multiplier',
            'trailing_stop': 'risk_management_trailing_stop',
            'trailing_stop_atr_multiplier': 'risk_management_trailing_stop_atr_multiplier',
            'min_atr_threshold': 'trade_filters_min_atr_threshold',
            'skip_lunch_hours': 'trade_filters_skip_lunch_hours',
            'lunch_start': 'trade_filters_lunch_start',
            'lunch_end': 'trade_filters_lunch_end'
        }
        
        # Map parameters using the mapping dictionary
        for param_key, value in params.items():
            if param_key in param_mapping:
                strategy_params[param_mapping[param_key]] = value
                logger.debug(f"Mapped {param_key} to {param_mapping[param_key]} with value {value}")
        
        # Convert lunch time strings to time objects if they exist
        if 'trade_filters_lunch_start' in strategy_params:
            lunch_start = datetime.strptime(strategy_params['trade_filters_lunch_start'], '%H:%M').time()
            lunch_end = datetime.strptime(strategy_params['trade_filters_lunch_end'], '%H:%M').time()
            strategy_params['trade_filters_lunch_start'] = lunch_start
            strategy_params['trade_filters_lunch_end'] = lunch_end
        
        # Log the final strategy parameters
        logger.info("Strategy parameters:")
        for key, value in strategy_params.items():
            logger.info(f"  {key}: {value}")
        
        # Initialize strategy with parameters
        strategy = SupertrendRsiStrategy(**strategy_params)
        
        # Generate sample data
        data = generate_sample_data(n=1000)
        
        # Initialize backtest engine with strategy
        engine = BacktestEngine(strategy=strategy)
        
        # Run backtest
        results = engine.run_backtest(data)
        
        # Add parameters to results
        for key, value in params.items():
            if isinstance(value, (int, float, str, bool)):
                results[key] = value
        
        return results
    
    except Exception as e:
        logger.error(f"Error in backtest: {str(e)}")
        return None

def run_all_backtests(param_grid):
    """Run backtests for all parameter combinations."""
    # Generate all parameter combinations
    param_combinations = generate_param_combinations(param_grid)
    logging.info(f"Generated {len(param_combinations)} parameter combinations")
    
    # Run backtests
    results = []
    for params in param_combinations:
        result = run_backtest(params)
        if result is not None:
            results.append(result)
    
    # Convert results to DataFrame
    if results:
        df_results = pd.DataFrame(results)
        
        # Sort by Sharpe ratio if it exists, otherwise by total profit
        if 'sharpe_ratio' in df_results.columns:
            df_results = df_results.sort_values('sharpe_ratio', ascending=False)
        elif 'total_profit' in df_results.columns:
            df_results = df_results.sort_values('total_profit', ascending=False)
        
        return df_results
    else:
        logging.warning("No valid results found from backtests")
        return pd.DataFrame()

def main():
    """Main function to run bulk backtests."""
    # Define parameter grid for testing
    param_grid = {
        'rsi_period': [14],
        'rsi_overbought': [65.0],  # Test with one value first
        'rsi_oversold': [35.0],    # Test with one value first
        'rsi_crossover': [True],
        'atr_period': [10],
        'atr_multiplier': [2.0],
        'ema_period': [200],
        'use_ema_filter': [False],
        'stop_loss_atr_multiplier': [1.5],
        'take_profit_atr_multiplier': [2.0],
        'trailing_stop': [True],
        'trailing_stop_atr_multiplier': [1.0],
        'min_atr_threshold': [0.0],  # Disable ATR threshold
        'skip_lunch_hours': [False],
        'lunch_start': ['12:00'],
        'lunch_end': ['13:30']
    }
    
    # Run backtests
    results = run_all_backtests(param_grid)
    
    # Save results
    if not results.empty:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results.to_csv(f'backtest_results_{timestamp}.csv', index=False)
        logger.info(f"Results saved to backtest_results_{timestamp}.csv")
        
        # Print top 5 results
        print("\nTop 5 Results:")
        print(results.head())
    else:
        logger.warning("No results to save")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main() 