import json
import threading
import paho.mqtt.client as mqtt
from typing import Callable, Optional

class MQTTClient:
    """
    Wrapper für paho-mqtt Client.
    Methoden:
      - connect(broker: str, port: int)
      - subscribe(topic: str, callback: Callable[[str, dict], None])
      - publish(topic: str, payload: dict)
      - loop_forever()
    """
    def __init__(self, client_id: Optional[str] = None):
        self.client = mqtt.Client(client_id or "")
        self._callbacks = {}

        self.client.on_message = self._on_message

    def connect(self, broker: str, port: int = 1883, keepalive: int = 60):
        """Verbindung zum Broker herstellen."""
        self.client.connect(broker, port, keepalive)

    def subscribe(self, topic: str, callback: Callable[[str, dict], None]):
        """
        Auf Topic abonnieren.
        callback(topic, payload_dict)
        """
        self._callbacks[topic] = callback
        self.client.subscribe(topic)

    def publish(self, topic: str, payload: dict):
        """JSON-payload an Topic senden."""
        message = json.dumps(payload)
        self.client.publish(topic, message)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            data = msg.payload.decode("utf-8")
        cb = self._callbacks.get(msg.topic)
        if cb:
            cb(msg.topic, data)

    def loop_forever(self):
        """Blocking loop zum Empfang von Nachrichten."""
        self.client.loop_forever()
