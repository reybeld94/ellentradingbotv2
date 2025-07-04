# EllenTradingBot v2

This repository contains a trading bot built with FastAPI and Alpaca. 

## Configuration

Alpaca credentials are now stored securely in the database instead of environment
variables.  You can create multiple portfolios and select the active one through
the API or from the frontend settings page.  Existing environment variables are
still used as a fallback when no portfolio is configured.
