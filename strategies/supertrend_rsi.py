import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, time
import logging
from backtest.config import STRATEGY_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupertrendRsiStrategy:
    """
    Enhanced trading strategy combining Supertrend, RSI, and EMA indicators
    with improved risk management and trade filters.
    """
    
    def __init__(
        self,
        rsi_period: int = STRATEGY_CONFIG['rsi']['period'],
        rsi_overbought: float = STRATEGY_CONFIG['rsi']['overbought'],
        rsi_oversold: float = STRATEGY_CONFIG['rsi']['oversold'],
        rsi_crossover: bool = STRATEGY_CONFIG['rsi']['use_crossover'],
        supertrend_atr_period: int = STRATEGY_CONFIG['supertrend']['atr_period'],
        supertrend_atr_multiplier: float = STRATEGY_CONFIG['supertrend']['atr_multiplier'],
        ema_period: int = STRATEGY_CONFIG['ema']['period'],
        ema_use_filter: bool = STRATEGY_CONFIG['ema']['use_ema_filter'],
        risk_management_stop_loss_atr_multiplier: float = STRATEGY_CONFIG['risk_management']['stop_loss_atr_multiplier'],
        risk_management_take_profit_atr_multiplier: float = STRATEGY_CONFIG['risk_management']['take_profit_atr_multiplier'],
        risk_management_trailing_stop: bool = STRATEGY_CONFIG['risk_management']['trailing_stop'],
        risk_management_trailing_stop_atr_multiplier: float = STRATEGY_CONFIG['risk_management']['trailing_stop_atr_multiplier'],
        trade_filters_min_atr_threshold: float = STRATEGY_CONFIG['trade_filters']['min_atr_threshold'],
        trade_filters_skip_lunch_hours: bool = STRATEGY_CONFIG['trade_filters']['skip_lunch_hours'],
        trade_filters_lunch_start: time = datetime.strptime(STRATEGY_CONFIG['trade_filters']['lunch_start'], '%H:%M').time(),
        trade_filters_lunch_end: time = datetime.strptime(STRATEGY_CONFIG['trade_filters']['lunch_end'], '%H:%M').time()
    ):
        """
        Initialize the strategy with custom parameters.
        """
        # RSI parameters
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.rsi_crossover = rsi_crossover
        
        # Supertrend parameters
        self.atr_period = supertrend_atr_period
        self.atr_multiplier = supertrend_atr_multiplier
        
        # EMA parameters
        self.ema_period = ema_period
        self.use_ema_filter = ema_use_filter
        
        # Risk management
        self.stop_loss_atr_multiplier = risk_management_stop_loss_atr_multiplier
        self.take_profit_atr_multiplier = risk_management_take_profit_atr_multiplier
        self.trailing_stop = risk_management_trailing_stop
        self.trailing_stop_atr_multiplier = risk_management_trailing_stop_atr_multiplier
        
        # Trade filters
        self.min_atr_threshold = trade_filters_min_atr_threshold
        self.skip_lunch_hours = trade_filters_skip_lunch_hours
        self.lunch_start = trade_filters_lunch_start
        self.lunch_end = trade_filters_lunch_end
        
        logger.info(f"Strategy initialized with parameters:")
        logger.info(f"RSI Period: {rsi_period}, Overbought: {rsi_overbought}, Oversold: {rsi_oversold}, Crossover: {rsi_crossover}")
        logger.info(f"ATR Period: {supertrend_atr_period}, Multiplier: {supertrend_atr_multiplier}, Min Threshold: {trade_filters_min_atr_threshold}")
        logger.info(f"EMA Period: {ema_period}, Use Filter: {ema_use_filter}")
        logger.info(f"Stop Loss ATR: {risk_management_stop_loss_atr_multiplier}, Take Profit ATR: {risk_management_take_profit_atr_multiplier}")
        logger.info(f"Trailing Stop: {risk_management_trailing_stop}, Trailing Stop ATR: {risk_management_trailing_stop_atr_multiplier}")
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator."""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        logger.debug(f"RSI range: min={rsi.min():.2f}, max={rsi.max():.2f}")
        return rsi
    
    def calculate_ema(self, data: pd.DataFrame) -> pd.Series:
        """Calculate EMA indicator."""
        ema = data['close'].ewm(span=self.ema_period, adjust=False).mean()
        return ema
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate ATR indicator."""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift(1))
        low_close = np.abs(data['low'] - data['close'].shift(1))
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # Handle NaN values in the first row
        true_range.iloc[0] = high_low.iloc[0]
        
        # Use exponential moving average for smoother ATR
        atr = true_range.ewm(span=self.atr_period, adjust=False).mean()
        
        # Ensure ATR is not zero to prevent division issues
        atr = atr.clip(lower=1e-10)
        
        logger.debug(f"ATR range: {atr.min():.2f} to {atr.max():.2f}")
        return atr
    
    def calculate_supertrend(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Supertrend indicator."""
        atr = self.calculate_atr(data)
        hl2 = (data['high'] + data['low']) / 2
        
        # Calculate upper and lower bands
        upperband = hl2 + (self.atr_multiplier * atr)
        lowerband = hl2 - (self.atr_multiplier * atr)
        
        # Initialize Supertrend
        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=int)
        
        # Set initial values
        supertrend.iloc[0] = upperband.iloc[0]
        direction.iloc[0] = 1
        
        # Calculate Supertrend
        for i in range(1, len(data)):
            curr_close = data['close'].iloc[i]
            prev_supertrend = supertrend.iloc[i-1]
            prev_direction = direction.iloc[i-1]
            curr_upperband = upperband.iloc[i]
            curr_lowerband = lowerband.iloc[i]
            
            # Determine trend direction
            if prev_supertrend <= curr_close:
                curr_direction = 1
            else:
                curr_direction = -1
            
            # Handle trend changes
            if curr_direction == 1:
                # Bullish trend
                if prev_direction == -1:  # Trend changed to bullish
                    curr_supertrend = curr_lowerband
                else:
                    curr_supertrend = max(curr_lowerband, prev_supertrend)
            else:
                # Bearish trend
                if prev_direction == 1:  # Trend changed to bearish
                    curr_supertrend = curr_upperband
                else:
                    curr_supertrend = min(curr_upperband, prev_supertrend)
            
            supertrend.iloc[i] = curr_supertrend
            direction.iloc[i] = curr_direction
        
        logger.debug(f"Supertrend direction changes: {np.sum(np.diff(direction) != 0)}")
        
        return pd.DataFrame({
            'supertrend': supertrend,
            'direction': direction
        })
    
    def is_lunch_time(self, timestamp: datetime) -> bool:
        """Check if the current time is during lunch hours."""
        if not self.skip_lunch_hours:
            return False
        
        current_time = timestamp.time()
        return self.lunch_start <= current_time <= self.lunch_end
    
    def generate_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        signals = []
        buy_signals = 0
        sell_signals = 0
        skipped_signals = 0
        
        # Calculate indicators
        rsi = self.calculate_rsi(data)
        ema = self.calculate_ema(data) if self.use_ema_filter else None
        atr = self.calculate_atr(data)
        supertrend = self.calculate_supertrend(data)
        
        # Calculate RSI crossovers if needed
        if self.rsi_crossover:
            rsi_above_oversold = (rsi > self.rsi_oversold) & (rsi.shift(1) <= self.rsi_oversold)
            rsi_below_overbought = (rsi < self.rsi_overbought) & (rsi.shift(1) >= self.rsi_overbought)
        
        in_position = False
        current_position = None
        
        # Determine warmup period
        warmup_periods = max(self.rsi_period, self.atr_period, self.ema_period if self.use_ema_filter else 0)
        
        logger.info(f"Starting signal generation with {len(data)} candles")
        logger.info(f"RSI range: {rsi.min():.2f} to {rsi.max():.2f}")
        logger.info(f"ATR range: {atr.min():.2f} to {atr.max():.2f}")
        
        for i in range(warmup_periods, len(data)):
            timestamp = data.index[i]
            current_price = data['close'].iloc[i]
            current_rsi = rsi.iloc[i]
            current_atr = atr.iloc[i]
            current_direction = supertrend['direction'].iloc[i]
            current_ema = ema.iloc[i] if self.use_ema_filter else None
            
            # Skip if during lunch hours
            if self.skip_lunch_hours and self.is_lunch_time(timestamp):
                skipped_signals += 1
                logger.debug(f"Skipped signal at {timestamp}: Lunch hours")
                continue
            
            # Skip if ATR is below threshold
            if current_atr < self.min_atr_threshold:
                skipped_signals += 1
                logger.debug(f"Skipped signal at {timestamp}: ATR {current_atr:.2f} below threshold {self.min_atr_threshold:.2f}")
                continue
            
            signal = {
                'timestamp': timestamp,
                'price': current_price,
                'rsi': current_rsi,
                'supertrend_direction': current_direction,
                'signal': 'HOLD',
                'reason': [],
                'stop_loss': None,
                'take_profit': None
            }
            
            # Generate buy signals
            if not in_position:
                # Initialize buy conditions based on RSI
                if self.rsi_crossover:
                    buy_condition = rsi.iloc[i] < self.rsi_oversold and rsi.iloc[i-1] >= self.rsi_oversold
                    logger.debug(f"Buy RSI crossover check: {rsi.iloc[i]:.2f} < {self.rsi_oversold} and {rsi.iloc[i-1]:.2f} >= {self.rsi_oversold}")
                else:
                    buy_condition = current_rsi <= self.rsi_oversold
                    logger.debug(f"Buy RSI check: {current_rsi:.2f} <= {self.rsi_oversold}")
                
                # Add Supertrend condition
                buy_condition = buy_condition and current_direction == 1
                logger.debug(f"Buy Supertrend check: direction {current_direction} == 1")
                
                # Check EMA filter if enabled
                if self.use_ema_filter:
                    buy_condition = buy_condition and current_price > current_ema
                    logger.debug(f"Buy EMA check: {current_price:.2f} > {current_ema:.2f}")
                
                if buy_condition:
                    signal['signal'] = 'BUY'
                    signal['reason'].append(f"RSI: {current_rsi:.2f}")
                    signal['stop_loss'] = current_price - (current_atr * self.stop_loss_atr_multiplier)
                    signal['take_profit'] = current_price + (current_atr * self.take_profit_atr_multiplier)
                    in_position = True
                    current_position = signal.copy()
                    buy_signals += 1
                    logger.info(f"Generated BUY signal at {timestamp}: RSI {current_rsi:.2f}, Price {current_price:.2f}")
            
            # Generate sell signals
            elif in_position:
                # Initialize sell conditions based on RSI
                if self.rsi_crossover:
                    sell_condition = rsi.iloc[i] > self.rsi_overbought and rsi.iloc[i-1] <= self.rsi_overbought
                    logger.debug(f"Sell RSI crossover check: {rsi.iloc[i]:.2f} > {self.rsi_overbought} and {rsi.iloc[i-1]:.2f} <= {self.rsi_overbought}")
                else:
                    sell_condition = current_rsi >= self.rsi_overbought
                    logger.debug(f"Sell RSI check: {current_rsi:.2f} >= {self.rsi_overbought}")
                
                # Add Supertrend condition
                sell_condition = sell_condition or current_direction == -1
                logger.debug(f"Sell Supertrend check: direction {current_direction} == -1")
                
                # Check stop loss and take profit
                if current_price <= current_position['stop_loss'] or current_price >= current_position['take_profit']:
                    sell_condition = True
                    logger.debug(f"Sell SL/TP check: Price {current_price:.2f}, SL {current_position['stop_loss']:.2f}, TP {current_position['take_profit']:.2f}")
                
                if sell_condition:
                    signal['signal'] = 'SELL'
                    signal['reason'].append(f"RSI: {current_rsi:.2f}")
                    in_position = False
                    current_position = None
                    sell_signals += 1
                    logger.info(f"Generated SELL signal at {timestamp}: RSI {current_rsi:.2f}, Price {current_price:.2f}")
            
            if signal['signal'] != 'HOLD':
                signals.append(signal)
        
        logger.info("Signal generation complete:")
        logger.info(f"Generated signals: {buy_signals} buy, {sell_signals} sell")
        logger.info(f"Skipped signals due to filters: {skipped_signals}")
        
        return signals 