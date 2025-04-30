# Algorithmic Trading Bot for Indian Markets

A Python-based algorithmic trading bot that implements a Supertrend + RSI strategy for Indian markets using Angel One's SmartAPI. The bot supports both paper trading and live trading modes, with a focus on risk management and performance tracking.

## Features

- **Advanced Trading Strategy**: Combines Supertrend and RSI indicators for robust signal generation
- **Paper Trading Support**: Test strategies without real money
- **Live Trading**: Connect to Angel One's SmartAPI for live market execution
- **Detailed Signal Logging**: Comprehensive signal generation with reasons
- **Portfolio Management**: Track positions, PnL, and performance metrics
- **Trade History**: Maintain detailed logs of all trades and portfolio states
- **Configurable Parameters**: Adjust strategy parameters and risk management rules

## Strategy Details

The bot implements a combined Supertrend and RSI strategy:

- **Supertrend Indicator**: 
  - Tracks price momentum and trend direction
  - Configurable ATR period and multiplier
  - Generates trend-following signals

- **RSI Indicator**:
  - Identifies overbought/oversold conditions
  - Customizable period and threshold levels
  - Provides mean reversion signals

Signals are generated when both indicators align:
- **Buy Signal**: Price above Supertrend + RSI oversold
- **Sell Signal**: Price below Supertrend + RSI overbought
- **Hold Signal**: When conditions don't align

## Project Structure

```
trading-bot/
├── api/                 # API connection and authentication
├── config/             # Configuration management
├── data/              # Data fetching and processing
├── execution/         # Trade execution logic
├── logs/              # Trade and portfolio logs
├── strategies/        # Trading strategies
├── utils/            # Helper functions
├── main.py           # API connection entry point
├── run_bot.py        # Main bot execution
└── requirements.txt   # Project dependencies
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your environment:
- Copy `.env.example` to `.env`
- Add your Angel One API credentials
- Adjust strategy parameters in `config/config.json`

## Usage

1. For paper trading:
```bash
python run_bot.py
```

2. For live trading (after proper configuration):
```bash
python main.py
```

## Configuration

The bot can be configured through:
- `.env` file for API credentials
- `config/config.json` for strategy parameters
- `run_bot.py` for execution settings

## Risk Management

- Position sizing based on portfolio percentage
- Maximum concurrent positions limit
- Slippage simulation in paper trading
- Detailed PnL tracking and reporting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS. 