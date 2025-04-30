import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable
from datetime import datetime
import json
import os
import mplfinance as mpf
import matplotlib.pyplot as plt
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Backtester:
    """
    Backtesting engine for trading strategies.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        position_size: float = 0.1,
        max_positions: int = 5,
        slippage: float = 0.001
    ):
        """
        Initialize the backtester.
        
        Args:
            initial_capital (float): Initial capital for trading
            position_size (float): Percentage of capital to use per trade
            max_positions (int): Maximum number of concurrent positions
            slippage (float): Simulated slippage percentage
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.max_positions = max_positions
        self.slippage = slippage
        
        # Initialize portfolio
        self.portfolio = {
            'capital': initial_capital,
            'exposure': 0.0,
            'positions': {},
            'total_trades': 0,
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'equity_curve': [],
            'max_drawdown': 0.0
        }
        
        # Trade history
        self.trade_history = []
        
    def calculate_position_size(self, price: float) -> int:
        """
        Calculate the number of shares to buy based on position size.
        
        Args:
            price (float): Current price of the instrument
            
        Returns:
            int: Number of shares to buy
        """
        amount = self.portfolio['capital'] * self.position_size
        return int(amount / price)
    
    def execute_trade(
        self,
        symbol: str,
        signal: str,
        price: float,
        timestamp: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a simulated trade based on the signal.
        
        Args:
            symbol (str): Trading symbol
            signal (str): Trading signal (BUY/SELL)
            price (float): Current price
            timestamp (datetime): Trade timestamp
            
        Returns:
            Optional[Dict[str, Any]]: Trade details if executed, None otherwise
        """
        # Apply slippage
        execution_price = price * (1 + self.slippage if signal == 'BUY' else 1 - self.slippage)
        
        if signal == 'BUY':
            # Check if we can open a new position
            if len(self.portfolio['positions']) >= self.max_positions:
                logger.warning(f"Cannot open new position for {symbol}: Maximum positions reached")
                return None
                
            # Calculate position size
            quantity = self.calculate_position_size(execution_price)
            if quantity == 0:
                logger.warning(f"Cannot open position for {symbol}: Insufficient capital")
                return None
                
            # Calculate cost
            cost = execution_price * quantity
            if cost > self.portfolio['capital']:
                logger.warning(f"Cannot open position for {symbol}: Insufficient capital")
                return None
                
            # Update portfolio
            self.portfolio['positions'][symbol] = {
                'quantity': quantity,
                'entry_price': execution_price,
                'entry_time': timestamp
            }
            self.portfolio['capital'] -= cost
            self.portfolio['exposure'] += cost
            self.portfolio['total_trades'] += 1
            
            trade = {
                'timestamp': timestamp,
                'symbol': symbol,
                'action': 'BUY',
                'quantity': quantity,
                'price': execution_price,
                'cost': cost,
                'pnl': 0.0
            }
            self.trade_history.append(trade)
            return trade
            
        elif signal == 'SELL':
            # Check if we have a position to close
            if symbol not in self.portfolio['positions']:
                logger.warning(f"No position to close for {symbol}")
                return None
                
            position = self.portfolio['positions'][symbol]
            quantity = position['quantity']
            entry_price = position['entry_price']
            
            # Calculate PnL
            pnl = (execution_price - entry_price) * quantity
            
            # Update portfolio
            self.portfolio['capital'] += execution_price * quantity
            self.portfolio['exposure'] -= entry_price * quantity
            self.portfolio['total_pnl'] += pnl
            
            if pnl > 0:
                self.portfolio['winning_trades'] += 1
            else:
                self.portfolio['losing_trades'] += 1
                
            del self.portfolio['positions'][symbol]
            
            trade = {
                'timestamp': timestamp,
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'price': execution_price,
                'cost': execution_price * quantity,
                'pnl': pnl
            }
            self.trade_history.append(trade)
            return trade
            
        return None
    
    def calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown from equity curve.
        
        Returns:
            float: Maximum drawdown percentage
        """
        if not self.portfolio['equity_curve']:
            return 0.0
            
        equity = np.array([point['equity'] for point in self.portfolio['equity_curve']])
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        return np.max(drawdown) * 100
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: Callable,
        symbol: str,
        interval: str
    ) -> Dict[str, Any]:
        """
        Run backtest on historical data.
        
        Args:
            data (pd.DataFrame): OHLCV data
            strategy (Callable): Strategy function
            symbol (str): Trading symbol
            interval (str): Time interval
            
        Returns:
            Dict[str, Any]: Backtest results
        """
        # Reset portfolio
        self.portfolio = {
            'capital': self.initial_capital,
            'exposure': 0.0,
            'positions': {},
            'total_trades': 0,
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'equity_curve': [],
            'max_drawdown': 0.0
        }
        self.trade_history = []
        
        # Generate signals
        signals = strategy(data)
        
        # Process each candle
        for i in range(len(data)):
            current_signal = signals[i]
            current_price = data['close'].iloc[i]
            current_time = data.index[i]
            
            # Update equity curve
            self.portfolio['equity_curve'].append({
                'timestamp': current_time,
                'equity': self.portfolio['capital'] + self.portfolio['exposure']
            })
            
            # Execute trade if signal is not HOLD
            if current_signal['signal'] != 'HOLD':
                self.execute_trade(
                    symbol=symbol,
                    signal=current_signal['signal'],
                    price=current_price,
                    timestamp=current_time
                )
        
        # Calculate final metrics
        self.portfolio['max_drawdown'] = self.calculate_max_drawdown()
        
        # Generate results
        results = {
            'symbol': symbol,
            'interval': interval,
            'start_date': data.index[0].strftime('%Y-%m-%d'),
            'end_date': data.index[-1].strftime('%Y-%m-%d'),
            'initial_capital': self.initial_capital,
            'final_capital': self.portfolio['capital'] + self.portfolio['exposure'],
            'total_pnl': self.portfolio['total_pnl'],
            'total_trades': self.portfolio['total_trades'],
            'winning_trades': self.portfolio['winning_trades'],
            'losing_trades': self.portfolio['losing_trades'],
            'win_rate': (self.portfolio['winning_trades'] / self.portfolio['total_trades'] * 100 
                        if self.portfolio['total_trades'] > 0 else 0),
            'max_drawdown': self.portfolio['max_drawdown'],
            'trade_history': self.trade_history
        }
        
        return results
    
    def generate_chart(
        self,
        data: pd.DataFrame,
        signals: List[Dict[str, Any]],
        symbol: str,
        interval: str,
        save_path: str
    ) -> None:
        """
        Generate and save candlestick chart with indicators.
        
        Args:
            data (pd.DataFrame): OHLCV data
            signals (List[Dict[str, Any]]): Trading signals
            symbol (str): Trading symbol
            interval (str): Time interval
            save_path (str): Path to save the chart
        """
        # Prepare data for mplfinance
        df = data.copy()
        df.index = pd.to_datetime(df.index)
        
        # Create buy/sell markers
        buy_signals = [i for i, s in enumerate(signals) if s['signal'] == 'BUY']
        sell_signals = [i for i, s in enumerate(signals) if s['signal'] == 'SELL']
        
        # Create markers
        markers = []
        for i in buy_signals:
            markers.append((i, '^', 'green'))
        for i in sell_signals:
            markers.append((i, 'v', 'red'))
        
        # Create figure
        fig, axes = mpf.plot(
            df,
            type='candle',
            style='charles',
            title=f'{symbol} {interval} Backtest Results',
            ylabel='Price',
            volume=True,
            returnfig=True
        )
        
        # Add markers
        for marker in markers:
            axes[0].plot(
                marker[0],
                df['close'].iloc[marker[0]],
                marker[1],
                color=marker[2],
                markersize=10
            )
        
        # Save chart
        plt.savefig(save_path)
        plt.close()
    
    def save_results(
        self,
        results: Dict[str, Any],
        save_dir: str
    ) -> None:
        """
        Save backtest results to JSON file.
        
        Args:
            results (Dict[str, Any]): Backtest results
            save_dir (str): Directory to save results
        """
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Save results
        filename = f"{results['symbol']}_{results['interval']}_{results['start_date']}_{results['end_date']}.json"
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=4, default=str)
        
        logger.info(f"Saved backtest results to {filepath}") 