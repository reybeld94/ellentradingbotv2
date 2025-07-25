# EllenTradingBot v2

This repository contains a trading bot built with FastAPI and uses Kraken as
its trading broker.

## Configuration

Broker credentials are stored securely in the database. Each user can create
their own portfolios from the frontend or via the API and select which one is
active. The application no longer falls back to environment variables for
credentials. Configuration now relies on environment variables provided by the
shell; a `.env` file is no longer loaded automatically.

If the `SECRET_KEY` environment variable is not set, the application will
generate a new key and store it in a `secret.key` file. Keeping this file
around ensures that encrypted portfolio credentials remain decryptable across
restarts.

Create a portfolio whose `base_url` contains `api.kraken.com` and provide your
Kraken API and secret keys. The library `python-kraken-sdk` is required and
listed in `requirements.txt`.
For trading with Alpaca, install the stable `alpaca-trade-api` package,
also included in `requirements.txt` and `app/requirements.txt`.

Each user has a **position_limit** value determining how many open positions they
may hold at once. The default limit is 7 and can be modified from the profile
page or via the API.

## Admin Setup

Before starting the server, create an initial admin user:

```bash
python scripts/create_admin_user.py --email you@example.com --username admin --password yourpassword
```
