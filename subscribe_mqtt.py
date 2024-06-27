import paho.mqtt.client as mqtt
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Define the MQTT broker details
broker = "broker.mqtt.cool"
port = 1883
topic = "NMEA_Lightning"

# Callback when the client receives a message
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected successfully")
        client.subscribe(topic)
        logging.info(f"Subscribed to topic: {topic}")
    else:
        logging.error(f"Connection failed with code {rc}")

# Callback when the client disconnects from the broker
def on_disconnect(client, userdata, rc):
    logging.info(f"Disconnected with result code {rc}")

# Initialize MQTT client
client = mqtt.Client(client_id="mqttx_subscriber", clean_session=True, protocol=mqtt.MQTTv311)

# Assign the callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Connect to the broker
client.connect(broker, port, 60)

# Start the loop to process received messages
logging.info(f"Subscribed to topic {topic}. Waiting for messages...")
client.loop_forever()
