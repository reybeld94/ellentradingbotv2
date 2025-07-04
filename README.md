# EllenTradingBot v2

This repository contains a trading bot built with FastAPI and Alpaca. 

## Configuration

The application reads its configuration from environment variables or a `.env` file. The Alpaca credentials can be configured per portfolio. Use the variable `ALPACA_PORTFOLIO` to select which portfolio is active. For each portfolio provide the following variables:

```
ALPACA_<PORTFOLIO>_API_KEY
ALPACA_<PORTFOLIO>_SECRET_KEY
ALPACA_<PORTFOLIO>_BASE_URL  # optional, defaults to paper trading URL
```

If `ALPACA_PORTFOLIO` is not set, the prefix `DEFAULT` is used. The settings also fall back to `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` and `ALPACA_BASE_URL` for compatibility.

After modifying environment variables, restart the application so the new credentials are loaded.
