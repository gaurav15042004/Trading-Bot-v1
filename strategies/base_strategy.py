from abc import ABC, abstractmethod
import pandas as pd
from typing import Literal

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    All concrete strategy implementations must inherit from this class.
    """
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Literal["BUY", "SELL", "HOLD"]:
        """
        Generate a trading signal based on the provided data.
        
        Args:
            data (pd.DataFrame): DataFrame containing OHLCV data
            
        Returns:
            Literal["BUY", "SELL", "HOLD"]: Trading signal
        """
        pass 