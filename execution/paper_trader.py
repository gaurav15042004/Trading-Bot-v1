import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaperTrader:
    """
    Simulates trade execution and manages paper trading portfolio.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        position_size: float = 0.1,  # 10% of capital per trade
        max_positions: int = 5,
        slippage: float = 0.001  # 0.1% slippage
    ):
        """
        Initialize the paper trader with trading parameters.
        
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
            'losing_trades': 0
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
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get current portfolio summary.
        
        Returns:
            Dict[str, Any]: Portfolio summary
        """
        return {
            'capital': self.portfolio['capital'],
            'exposure': self.portfolio['exposure'],
            'positions': self.portfolio['positions'],
            'total_trades': self.portfolio['total_trades'],
            'total_pnl': self.portfolio['total_pnl'],
            'winning_trades': self.portfolio['winning_trades'],
            'losing_trades': self.portfolio['losing_trades'],
            'win_rate': (self.portfolio['winning_trades'] / self.portfolio['total_trades'] * 100 
                        if self.portfolio['total_trades'] > 0 else 0)
        }
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        Get complete trade history.
        
        Returns:
            List[Dict[str, Any]]: List of all trades
        """
        return self.trade_history 