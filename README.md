# Ellen Trading Bot v2

This project exposes several FastAPI endpoints to receive TradingView webhooks and execute orders. Below are instructions on configuring the `webhook_api_key`, adding strategies, and formatting webhook requests from TradingView.

## Configuring `webhook_api_key`

The API key is required when calling the public webhook endpoint (`/api/v1/webhook-public`). The default value is defined in `app/config.py` and can be overridden using an environment variable or `.env` file:

```python
webhook_api_key: Optional[str] = "ELLENTRADING0408"
```

To change it, set `WEBHOOK_API_KEY` in your environment (or within `.env`) to the desired value before starting the server.

## Adding Strategies

Strategies are stored in the `strategies` table. You can manage them through the API or by inserting directly into the database.

### Using the API

Authenticated users can create strategies via:

```
POST /api/v1/strategies
{
  "name": "my_strategy",
  "description": "Example description"
}
```

Strategies can also be listed (`GET /api/v1/strategies`), updated (`PUT /api/v1/strategies/{id}`) and deleted (`DELETE /api/v1/strategies/{id}`).

### Manual DB Insert

If you prefer to insert a strategy manually, connect to the database defined by `DATABASE_URL` (defaults to `sqlite:///./trading_bot.db`) and run:

```sql
INSERT INTO strategies (name, description) VALUES ('my_strategy', 'Example description');
```

## TradingView Webhook Format

TradingView should send a JSON payload that matches the `TradingViewWebhook` schema. Required fields are `symbol`, `action`, and `strategy_id`. Optional fields include `quantity`, `price`, `reason`, `confidence`, `timestamp`, and `message`.

Example payload:

```json
{
  "symbol": "BTCUSD",
  "action": "buy",
  "strategy_id": "my_strategy",
  "quantity": 1,
  "price": 43000,
  "reason": "fibonacci_entry",
  "confidence": 80,
  "timestamp": "{{timenow}}"
}
```

### Calling `/api/v1/webhook-public`

Include the API key either as a query parameter (`?api_key=YOUR_KEY`) or as the `X-API-Key` header. The endpoint will reject requests without a valid key.

```bash
curl -X POST "http://<server>/api/v1/webhook-public?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSD","action":"buy","strategy_id":"my_strategy"}'
```

Alternatively:

```bash
curl -X POST "http://<server>/api/v1/webhook-public" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"symbol":"BTCUSD","action":"buy","strategy_id":"my_strategy"}'
```

TradingView's webhook URL should include the query parameter or the custom header as shown above.

