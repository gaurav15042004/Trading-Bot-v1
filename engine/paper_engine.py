import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaperEngine:
    """
    Paper trading engine for simulating trades and tracking performance.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize the paper trading engine.
        
        Args:
            initial_capital (float): Initial capital for trading
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.current_exposure = 0.0
        
    def execute_trade(
        self,
        symbol: str,
        signal: str,
        price: float,
        quantity: int = 1,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Execute a paper trade based on the signal.
        
        Args:
            symbol (str): Trading symbol
            signal (str): Trading signal ("BUY" or "SELL")
            price (float): Current price
            quantity (int): Number of shares to trade
            timestamp (Optional[datetime]): Trade timestamp
            
        Returns:
            bool: True if trade was executed successfully
        """
        if not timestamp:
            timestamp = datetime.now()
            
        trade_value = price * quantity
        
        try:
            if signal == "BUY":
                if trade_value > self.capital:
                    logger.warning(f"Insufficient capital for BUY order: {trade_value} > {self.capital}")
                    return False
                    
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': timestamp
                }
                self.capital -= trade_value
                self.current_exposure += trade_value
                
                logger.info(f"Executed BUY order: {quantity} {symbol} @ {price}")
                
            elif signal == "SELL":
                if symbol not in self.positions:
                    logger.warning(f"No position found for SELL order: {symbol}")
                    return False
                    
                position = self.positions[symbol]
                pnl = (price - position['entry_price']) * quantity
                
                self.trade_history.append({
                    'symbol': symbol,
                    'entry_time': position['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': position['entry_price'],
                    'exit_price': price,
                    'quantity': quantity,
                    'pnl': pnl
                })
                
                self.capital += trade_value + pnl
                self.current_exposure -= trade_value
                del self.positions[symbol]
                
                logger.info(f"Executed SELL order: {quantity} {symbol} @ {price}, P&L: {pnl}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return False
            
    def get_portfolio_summary(self) -> Dict:
        """
        Get current portfolio summary.
        
        Returns:
            Dict: Portfolio summary including capital, exposure, and positions
        """
        return {
            'capital': self.capital,
            'exposure': self.current_exposure,
            'positions': self.positions,
            'total_trades': len(self.trade_history),
            'total_pnl': sum(trade['pnl'] for trade in self.trade_history)
        }
        
    def get_trade_history(self) -> pd.DataFrame:
        """
        Get trade history as a DataFrame.
        
        Returns:
            pd.DataFrame: Trade history with all executed trades
        """
        return pd.DataFrame(self.trade_history) 