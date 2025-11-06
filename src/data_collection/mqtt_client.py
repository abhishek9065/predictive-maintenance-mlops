"""
MQTT Client for IoT Data Collection
Handles MQTT protocol communication with IoT devices.
"""

import json
import time
from datetime import datetime
from typing import Callable, Optional
import paho.mqtt.client as mqtt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTDataCollector:
    """MQTT client for collecting sensor data from IoT devices."""
    
    def __init__(self, broker_address: str, port: int = 1883, 
                 client_id: Optional[str] = None):
        """
        Initialize MQTT client.
        
        Args:
            broker_address: MQTT broker address
            port: MQTT broker port
            client_id: Unique client identifier
        """
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id or f"mqtt_collector_{int(time.time())}"
        
        self.client = mqtt.Client(self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.message_callback = None
        self.is_connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when client connects to broker."""
        if rc == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT broker: {self.broker_address}:{self.port}")
        else:
            logger.error(f"Connection failed with code: {rc}")
    
    def _on_message(self, client, userdata, message):
        """Callback when message is received."""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode())
            
            logger.debug(f"Received message on topic '{topic}': {payload}")
            
            # Add metadata
            payload['mqtt_topic'] = topic
            payload['received_at'] = datetime.now().isoformat()
            
            # Call custom callback if registered
            if self.message_callback:
                self.message_callback(payload)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects from broker."""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect. Return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def connect(self, username: Optional[str] = None, 
                password: Optional[str] = None):
        """
        Connect to MQTT broker.
        
        Args:
            username: MQTT username
            password: MQTT password
        """
        try:
            if username and password:
                self.client.username_pw_set(username, password)
            
            logger.info(f"Connecting to MQTT broker at {self.broker_address}:{self.port}...")
            self.client.connect(self.broker_address, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not self.is_connected:
                raise ConnectionError("Failed to connect within timeout period")
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def subscribe(self, topic: str, qos: int = 0):
        """
        Subscribe to a topic.
        
        Args:
            topic: MQTT topic to subscribe to
            qos: Quality of Service level (0, 1, or 2)
        """
        if not self.is_connected:
            raise ConnectionError("Client is not connected to broker")
        
        self.client.subscribe(topic, qos)
        logger.info(f"Subscribed to topic: {topic} (QoS: {qos})")
    
    def publish(self, topic: str, payload: dict, qos: int = 0):
        """
        Publish a message to a topic.
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload (dict)
            qos: Quality of Service level
        """
        if not self.is_connected:
            raise ConnectionError("Client is not connected to broker")
        
        message = json.dumps(payload)
        result = self.client.publish(topic, message, qos)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published to topic '{topic}': {payload}")
        else:
            logger.error(f"Failed to publish message. Return code: {result.rc}")
    
    def set_message_callback(self, callback: Callable):
        """
        Set custom callback for processing messages.
        
        Args:
            callback: Function to call when message is received
        """
        self.message_callback = callback
    
    def run(self, blocking: bool = True):
        """
        Run the MQTT client loop.
        
        Args:
            blocking: Whether to run in blocking mode
        """
        if blocking:
            logger.info("Starting MQTT client loop (blocking)...")
            self.client.loop_forever()
        else:
            logger.info("MQTT client loop running in background")


class IoTDeviceSimulator:
    """Simulates an IoT device publishing sensor data via MQTT."""
    
    def __init__(self, mqtt_client: MQTTDataCollector, device_id: str):
        """
        Initialize device simulator.
        
        Args:
            mqtt_client: MQTT client instance
            device_id: Unique device identifier
        """
        self.mqtt_client = mqtt_client
        self.device_id = device_id
        self.topic = f"sensors/{device_id}"
    
    def publish_sensor_data(self, sensor_data: dict):
        """
        Publish sensor data to MQTT broker.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        """
        payload = {
            'device_id': self.device_id,
            'timestamp': datetime.now().isoformat(),
            'data': sensor_data
        }
        
        self.mqtt_client.publish(self.topic, payload)
    
    def simulate_continuous_data(self, interval_seconds: int = 5, 
                                duration_seconds: int = 60):
        """
        Simulate continuous sensor data publishing.
        
        Args:
            interval_seconds: Time between publishes
            duration_seconds: Total simulation duration
        """
        import random
        
        logger.info(f"Starting data simulation for device {self.device_id}")
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds:
            # Generate random sensor data
            sensor_data = {
                'temperature': round(random.uniform(20, 80), 2),
                'vibration': round(random.uniform(0, 10), 2),
                'pressure': round(random.uniform(80, 120), 2),
                'current': round(random.uniform(0, 50), 2)
            }
            
            self.publish_sensor_data(sensor_data)
            time.sleep(interval_seconds)
        
        logger.info(f"Data simulation completed for device {self.device_id}")


def main():
    """Main function for testing MQTT client."""
    # Initialize MQTT client
    mqtt_client = MQTTDataCollector(
        broker_address="test.mosquitto.org",  # Public test broker
        port=1883
    )
    
    # Define message handler
    def handle_message(message):
        logger.info(f"Processing message: {message}")
    
    mqtt_client.set_message_callback(handle_message)
    
    # Connect and subscribe
    mqtt_client.connect()
    mqtt_client.subscribe("sensors/#")
    
    # Simulate device
    device = IoTDeviceSimulator(mqtt_client, "PUMP_001")
    
    try:
        # Publish some test data
        device.simulate_continuous_data(interval_seconds=2, duration_seconds=10)
        
        # Keep listening
        time.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    finally:
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
