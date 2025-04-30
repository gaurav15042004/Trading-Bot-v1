import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradeLogger:
    """
    Handles logging of trades to CSV files.
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the trade logger.
        
        Args:
            log_dir (str): Directory to store trade logs
        """
        self.log_dir = log_dir
        self.trades_file = os.path.join(log_dir, "trades.csv")
        self.portfolio_file = os.path.join(log_dir, "portfolio.csv")
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize trade log file if it doesn't exist
        if not os.path.exists(self.trades_file):
            pd.DataFrame(columns=[
                'timestamp', 'symbol', 'action', 'quantity',
                'price', 'cost', 'pnl'
            ]).to_csv(self.trades_file, index=False)
            
        # Initialize portfolio log file if it doesn't exist
        if not os.path.exists(self.portfolio_file):
            pd.DataFrame(columns=[
                'timestamp', 'capital', 'exposure',
                'total_trades', 'total_pnl', 'win_rate'
            ]).to_csv(self.portfolio_file, index=False)
    
    def log_trade(self, trade: Dict[str, Any]) -> None:
        """
        Log a single trade to the trades CSV file.
        
        Args:
            trade (Dict[str, Any]): Trade details
        """
        try:
            # Convert trade to DataFrame
            trade_df = pd.DataFrame([{
                'timestamp': trade['timestamp'],
                'symbol': trade['symbol'],
                'action': trade['action'],
                'quantity': trade['quantity'],
                'price': trade['price'],
                'cost': trade['cost'],
                'pnl': trade['pnl']
            }])
            
            # Append to CSV
            trade_df.to_csv(self.trades_file, mode='a', header=False, index=False)
            logger.info(f"Logged trade: {trade['action']} {trade['quantity']} {trade['symbol']} @ {trade['price']}")
            
        except Exception as e:
            logger.error(f"Error logging trade: {str(e)}")
    
    def log_portfolio(self, portfolio: Dict[str, Any]) -> None:
        """
        Log portfolio state to the portfolio CSV file.
        
        Args:
            portfolio (Dict[str, Any]): Portfolio details
        """
        try:
            # Convert portfolio to DataFrame
            portfolio_df = pd.DataFrame([{
                'timestamp': datetime.now(),
                'capital': portfolio['capital'],
                'exposure': portfolio['exposure'],
                'total_trades': portfolio['total_trades'],
                'total_pnl': portfolio['total_pnl'],
                'win_rate': portfolio['win_rate']
            }])
            
            # Append to CSV
            portfolio_df.to_csv(self.portfolio_file, mode='a', header=False, index=False)
            logger.info("Logged portfolio state")
            
        except Exception as e:
            logger.error(f"Error logging portfolio: {str(e)}")
    
    def get_trade_history(self) -> pd.DataFrame:
        """
        Get complete trade history from CSV.
        
        Returns:
            pd.DataFrame: Trade history
        """
        try:
            return pd.read_csv(self.trades_file)
        except Exception as e:
            logger.error(f"Error reading trade history: {str(e)}")
            return pd.DataFrame()
    
    def get_portfolio_history(self) -> pd.DataFrame:
        """
        Get complete portfolio history from CSV.
        
        Returns:
            pd.DataFrame: Portfolio history
        """
        try:
            return pd.read_csv(self.portfolio_file)
        except Exception as e:
            logger.error(f"Error reading portfolio history: {str(e)}")
            return pd.DataFrame() 