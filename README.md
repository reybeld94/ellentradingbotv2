# EllenTradingBot v2

This repository contains a trading bot built with FastAPI and Alpaca. 

## Configuration

Alpaca credentials are stored securely in the database. Each user can create
their own portfolios from the frontend or via the API and select which one is
active. The application no longer falls back to environment variables for
credentials.
