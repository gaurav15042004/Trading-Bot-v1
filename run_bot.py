import time
import logging
from datetime import datetime, timedelta
from typing import Dict

from config.config_loader import ConfigLoader
from api.smart_api_manager import SmartAPIManager
from data.data_manager import DataManager
from strategies.supertrend_rsi_strategy import SupertrendRsiStrategy
from execution.paper_trader import PaperTrader
from logs.trade_logger import TradeLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBot:
    """
    Main trading bot class that orchestrates the trading process.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the trading bot with configuration.
        
        Args:
            config (Dict): Configuration dictionary
        """
        self.config = config
        self.api_manager = SmartAPIManager(config)
        self.data_manager = DataManager(self.api_manager)
        self.strategy = SupertrendRsiStrategy()
        self.paper_trader = PaperTrader(
            initial_capital=config.get('initial_capital', 100000.0),
            position_size=config.get('position_size', 0.1),
            max_positions=config.get('max_positions', 5),
            slippage=config.get('slippage', 0.001)
        )
        self.trade_logger = TradeLogger()
        
    def run(self, symbol: str = "NIFTY", interval: str = "FIVE_MINUTE"):
        """
        Run the trading bot with the specified symbol and interval.
        
        Args:
            symbol (str): Trading symbol
            interval (str): Time interval for data
        """
        logger.info(f"Starting trading bot for {symbol} with {interval} interval")
        
        try:
            while True:
                # Fetch historical data
                from_date = datetime.now() - timedelta(days=1)
                data = self.data_manager.fetch_historical_data(
                    symbol=symbol,
                    exchange="NSE",
                    interval=interval,
                    from_date=from_date
                )
                
                # Generate detailed signals
                signals = self.strategy.generate_detailed_signals(data)
                latest_signal = signals[-1]  # Get the most recent signal
                
                # Execute trade if signal is not HOLD
                if latest_signal['signal'] != "HOLD":
                    trade = self.paper_trader.execute_trade(
                        symbol=symbol,
                        signal=latest_signal['signal'],
                        price=latest_signal['price'],
                        timestamp=latest_signal['timestamp']
                    )
                    
                    if trade:
                        # Log the trade
                        self.trade_logger.log_trade(trade)
                        logger.info(f"Executed {trade['action']} trade for {symbol}: {trade['quantity']} @ {trade['price']}")
                
                # Get and log portfolio summary
                portfolio = self.paper_trader.get_portfolio_summary()
                self.trade_logger.log_portfolio(portfolio)
                logger.info(f"Portfolio Summary: {portfolio}")
                
                # Log signal details
                logger.info(f"Latest Signal: {latest_signal['signal']} - Reasons: {', '.join(latest_signal['reason'])}")
                
                # Wait for next interval
                time.sleep(300)  # 5 minutes
                
        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
        except Exception as e:
            logger.error(f"Error in trading bot: {str(e)}")
        finally:
            self.api_manager.logout()
            
            # Print final summary
            portfolio = self.paper_trader.get_portfolio_summary()
            logger.info("\nFinal Portfolio Summary:")
            logger.info(f"Initial Capital: {self.paper_trader.initial_capital}")
            logger.info(f"Final Capital: {portfolio['capital']}")
            logger.info(f"Total PnL: {portfolio['total_pnl']}")
            logger.info(f"Total Trades: {portfolio['total_trades']}")
            logger.info(f"Win Rate: {portfolio['win_rate']:.2f}%")

def main():
    """Main entry point for the trading bot."""
    try:
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        
        # Initialize and run trading bot
        bot = TradingBot(config)
        bot.run()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main() 