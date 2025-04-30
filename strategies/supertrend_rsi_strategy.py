import pandas as pd
import numpy as np
from typing import Literal, Dict, Any, List
from .base_strategy import BaseStrategy

class SupertrendRsiStrategy(BaseStrategy):
    """
    Trading strategy combining Supertrend and RSI indicators.
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        atr_period: int = 10,
        atr_multiplier: float = 3.0
    ):
        """
        Initialize the strategy with custom parameters.
        
        Args:
            rsi_period (int): Period for RSI calculation
            rsi_overbought (float): RSI level considered overbought
            rsi_oversold (float): RSI level considered oversold
            atr_period (int): Period for ATR calculation in Supertrend
            atr_multiplier (float): Multiplier for ATR in Supertrend
        """
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator."""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_supertrend(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Supertrend indicator."""
        atr = data['high'].rolling(self.atr_period).max() - data['low'].rolling(self.atr_period).min()
        basic_upper = (data['high'] + data['low']) / 2 + self.atr_multiplier * atr
        basic_lower = (data['high'] + data['low']) / 2 - self.atr_multiplier * atr
        
        final_upper = basic_upper.copy()
        final_lower = basic_lower.copy()
        
        for i in range(1, len(data)):
            if basic_upper.iloc[i] < final_upper.iloc[i-1] and data['close'].iloc[i-1] <= final_upper.iloc[i-1]:
                final_upper.iloc[i] = final_upper.iloc[i-1]
            if basic_lower.iloc[i] > final_lower.iloc[i-1] and data['close'].iloc[i-1] >= final_lower.iloc[i-1]:
                final_lower.iloc[i] = final_lower.iloc[i-1]
                
        supertrend = pd.Series(index=data.index, dtype=float)
        for i in range(len(data)):
            if i == 0:
                supertrend.iloc[i] = 0
            elif supertrend.iloc[i-1] == final_upper.iloc[i-1] and data['close'].iloc[i] <= final_upper.iloc[i]:
                supertrend.iloc[i] = final_upper.iloc[i]
            elif supertrend.iloc[i-1] == final_upper.iloc[i-1] and data['close'].iloc[i] > final_upper.iloc[i]:
                supertrend.iloc[i] = final_lower.iloc[i]
            elif supertrend.iloc[i-1] == final_lower.iloc[i-1] and data['close'].iloc[i] >= final_lower.iloc[i]:
                supertrend.iloc[i] = final_lower.iloc[i]
            elif supertrend.iloc[i-1] == final_lower.iloc[i-1] and data['close'].iloc[i] < final_lower.iloc[i]:
                supertrend.iloc[i] = final_upper.iloc[i]
                
        return pd.DataFrame({
            'supertrend': supertrend,
            'direction': np.where(data['close'] > supertrend, 1, -1)
        })
    
    def generate_signal(self, data: pd.DataFrame) -> Literal["BUY", "SELL", "HOLD"]:
        """
        Generate trading signal based on Supertrend and RSI indicators.
        
        Args:
            data (pd.DataFrame): DataFrame containing OHLCV data
            
        Returns:
            Literal["BUY", "SELL", "HOLD"]: Trading signal
        """
        # Calculate indicators
        rsi = self.calculate_rsi(data)
        supertrend = self.calculate_supertrend(data)
        
        # Get latest values
        current_rsi = rsi.iloc[-1]
        current_direction = supertrend['direction'].iloc[-1]
        
        # Generate signal
        if current_direction == 1 and current_rsi < self.rsi_oversold:
            return "BUY"
        elif current_direction == -1 and current_rsi > self.rsi_overbought:
            return "SELL"
        else:
            return "HOLD"
            
    def generate_detailed_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate detailed trading signals for each candle with reasons.
        
        Args:
            data (pd.DataFrame): DataFrame containing OHLCV data
            
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing signal details
        """
        # Calculate indicators
        rsi = self.calculate_rsi(data)
        supertrend = self.calculate_supertrend(data)
        
        signals = []
        for i in range(len(data)):
            current_rsi = rsi.iloc[i]
            current_direction = supertrend['direction'].iloc[i]
            current_price = data['close'].iloc[i]
            
            signal = {
                'timestamp': data.index[i],
                'price': current_price,
                'rsi': current_rsi,
                'supertrend_direction': current_direction,
                'signal': 'HOLD',
                'reason': []
            }
            
            # Check for buy signal
            if current_direction == 1 and current_rsi < self.rsi_oversold:
                signal['signal'] = 'BUY'
                signal['reason'].append(f'RSI oversold ({current_rsi:.2f} < {self.rsi_oversold})')
                signal['reason'].append('Price above supertrend')
            
            # Check for sell signal
            elif current_direction == -1 and current_rsi > self.rsi_overbought:
                signal['signal'] = 'SELL'
                signal['reason'].append(f'RSI overbought ({current_rsi:.2f} > {self.rsi_overbought})')
                signal['reason'].append('Price below supertrend')
            
            # If no signal, add reason for holding
            if signal['signal'] == 'HOLD':
                if current_direction == 1:
                    signal['reason'].append('Price above supertrend')
                else:
                    signal['reason'].append('Price below supertrend')
                    
                if current_rsi > self.rsi_oversold:
                    signal['reason'].append(f'RSI not oversold ({current_rsi:.2f} > {self.rsi_oversold})')
                elif current_rsi < self.rsi_overbought:
                    signal['reason'].append(f'RSI not overbought ({current_rsi:.2f} < {self.rsi_overbought})')
                else:
                    signal['reason'].append(f'RSI in neutral zone ({self.rsi_oversold} < {current_rsi:.2f} < {self.rsi_overbought})')
            
            signals.append(signal)
            
        return signals 