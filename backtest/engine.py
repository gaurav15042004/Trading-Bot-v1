import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from .config import BACKTEST_CONFIG, STRATEGY_CONFIG
import logging

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, strategy):
        from strategies.supertrend_rsi import SupertrendRsiStrategy
        if not isinstance(strategy, SupertrendRsiStrategy):
            raise ValueError("Strategy must be an instance of SupertrendRsiStrategy")
        self.strategy = strategy
        self.config = BACKTEST_CONFIG
        self.initial_capital = self.config['initial_capital']
        self.position_size = self.config['position_size']
        self.max_positions = self.config['max_positions']
        self.slippage = self.config['slippage']
        self.commission = self.config['commission']
        
        # Initialize portfolio state
        self.reset_portfolio()
    
    def reset_portfolio(self):
        """Reset portfolio state."""
        self.capital = self.initial_capital
        self.positions = {}  # Current open positions
        self.trades = []  # List of completed trades
        self.portfolio_value = []  # Historical portfolio values
        self.trade_history = []  # Detailed trade history
    
    def calculate_position_size(self, price: float) -> int:
        """Calculate position size based on available capital."""
        # Calculate the maximum number of units we can buy
        max_units = self.capital / price
        
        # Calculate the target number of units based on position size
        target_units = max_units * self.position_size
        
        # Round down to the nearest integer, but ensure at least 1 unit if we have enough capital
        if target_units >= 0.5:  # If we can afford at least half a unit
            return max(1, int(target_units))
        return 0
    
    def execute_trade(self, symbol: str, signal: str, price: float, timestamp: datetime):
        """Execute a trade based on the signal."""
        print(f"Processing {signal} signal for {symbol} at ₹{price:,.2f}")
        print(f"Current capital: ₹{self.capital:,.2f}")
        
        if signal == 'BUY' and len(self.positions) < self.max_positions:
            # Calculate position size
            quantity = self.calculate_position_size(price)
            if quantity == 0:
                print(f"Trade skipped: Cannot afford minimum position (Price: ₹{price:,.2f})")
                return
            
            # Calculate costs
            cost = price * quantity
            commission = cost * self.commission
            slippage = cost * self.slippage
            total_cost = cost + commission + slippage
            
            print(f"Trade details: {quantity} units at ₹{price:,.2f}, Total Cost: ₹{total_cost:,.2f}")
            
            if total_cost <= self.capital:
                # Open position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': timestamp,
                    'entry_cost': total_cost
                }
                self.capital -= total_cost
                
                print(f"BUY executed: {quantity} {symbol} at ₹{price:,.2f}")
                print(f"Remaining capital: ₹{self.capital:,.2f}")
                
                # Record trade
                self.trade_history.append({
                    'symbol': symbol,
                    'type': 'BUY',
                    'quantity': quantity,
                    'price': price,
                    'cost': total_cost,
                    'timestamp': timestamp
                })
            else:
                print(f"Trade skipped: Insufficient capital (Required: ₹{total_cost:,.2f}, Available: ₹{self.capital:,.2f})")
        
        elif signal == 'SELL' and symbol in self.positions:
            position = self.positions[symbol]
            quantity = position['quantity']
            
            # Calculate proceeds
            proceeds = price * quantity
            commission = proceeds * self.commission
            slippage = proceeds * self.slippage
            net_proceeds = proceeds - commission - slippage
            
            # Close position
            profit_loss = net_proceeds - position['entry_cost']
            self.capital += net_proceeds
            del self.positions[symbol]
            
            print(f"SELL executed: {quantity} {symbol} at ₹{price:,.2f}")
            print(f"P/L: ₹{profit_loss:,.2f} ({(profit_loss/position['entry_cost'])*100:.2f}%)")
            
            # Record trade
            self.trade_history.append({
                'symbol': symbol,
                'type': 'SELL',
                'quantity': quantity,
                'price': price,
                'proceeds': net_proceeds,
                'profit_loss': profit_loss,
                'timestamp': timestamp
            })
            
            # Record completed trade
            self.trades.append({
                'symbol': symbol,
                'entry_time': position['entry_time'],
                'exit_time': timestamp,
                'entry_price': position['entry_price'],
                'exit_price': price,
                'quantity': quantity,
                'profit_loss': profit_loss,
                'return_pct': (profit_loss / position['entry_cost']) * 100
            })
        else:
            print(f"Trade skipped: Invalid signal or position state (Signal: {signal}, In Position: {symbol in self.positions})")
    
    def run_backtest(self, data: pd.DataFrame):
        """Run backtest on historical data."""
        self.reset_portfolio()
        logger.info(f"Starting backtest with {len(data)} bars")
        
        # Generate signals
        signals = self.strategy.generate_signals(data)
        logger.info(f"Generated {len(signals)} signals")
        
        # Create a dictionary for faster signal lookup
        signal_dict = {signal['timestamp']: signal for signal in signals}
        
        # Process each bar
        for i in range(len(data)):
            timestamp = data.index[i]
            price = data['close'].iloc[i]
            
            # Get signal for current timestamp
            signal_info = signal_dict.get(timestamp)
            current_signal = signal_info['signal'] if signal_info else None
            
            # Execute trades based on signals
            if current_signal and current_signal != 'HOLD':
                logger.debug(f"Processing signal at {timestamp}: {current_signal} at price {price}")
                self.execute_trade('NIFTY', current_signal, price, timestamp)
            
            # Calculate portfolio value
            position_value = sum(
                pos['quantity'] * price
                for pos in self.positions.values()
            )
            total_value = self.capital + position_value
            self.portfolio_value.append({
                'timestamp': timestamp,
                'value': total_value
            })
        
        return self.get_results()
    
    def get_results(self) -> Dict[str, Any]:
        """Calculate and return backtest results."""
        # Initialize default results
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_profit_loss': 0.0,
            'avg_profit_per_trade': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'trades': [],
            'portfolio_values': self.portfolio_value
        }
        
        if not self.trades:
            return results
        
        # Calculate basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['profit_loss'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate profit metrics
        total_profit_loss = sum(t['profit_loss'] for t in self.trades)
        avg_profit_per_trade = total_profit_loss / total_trades
        
        # Calculate portfolio returns
        portfolio_values = pd.DataFrame(self.portfolio_value)
        portfolio_values.set_index('timestamp', inplace=True)
        returns = portfolio_values['value'].pct_change().dropna()
        
        # Calculate risk metrics
        max_drawdown = (portfolio_values['value'].max() - portfolio_values['value'].min()) / portfolio_values['value'].max()
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
        
        # Update results
        results.update({
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit_loss': total_profit_loss,
            'avg_profit_per_trade': avg_profit_per_trade,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trades': self.trades
        })
        
        return results 