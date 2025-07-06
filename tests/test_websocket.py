import asyncio
import json
import os
from fastapi.testclient import TestClient

os.environ.setdefault('SECRET_KEY', 'secret')

from app.main import app
from app.websockets import ws_manager

client = TestClient(app)

def test_websocket_broadcast():
    with client.websocket_connect("/ws/updates") as websocket:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ws_manager.broadcast(json.dumps({"event": "test"})))
        data = websocket.receive_text()
        assert "\"event\": \"test\"" in data
