import paho.mqtt.client as mqtt
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Define the MQTT broker details
broker = "broker.mqtt.cool"
port = 1883
topic = "NMEA_Lightning"

# Example NMEA sentences to publish
strike_sentence = "$WIMLI,100,120,3.5*1F\r\n"
noise_sentence = "$WIMLN*4A\r\n"
status_sentence = "$WIMSU,10,20,1,0,1,0*2C\r\n"

# Initialize MQTT client
client = mqtt.Client(client_id="mqttx_publisher", clean_session=True, protocol=mqtt.MQTTv311)

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected successfully")
    else:
        logging.error(f"Connection failed with code {rc}")

# Callback when the client publishes a message
def on_publish(client, userdata, mid):
    logging.info(f"Message {mid} published successfully")

# Assign the callbacks
client.on_connect = on_connect
client.on_publish = on_publish

# Connect to the broker
client.connect(broker, port, 60)

# Start the loop to process the callbacks
client.loop_start()

# Publish messages
result = client.publish(topic, strike_sentence)
result.wait_for_publish()
if result.rc == mqtt.MQTT_ERR_SUCCESS:
    logging.info("Strike sentence published successfully")
else:
    logging.error(f"Failed to publish strike sentence: {result.rc}")

result = client.publish(topic, noise_sentence)
result.wait_for_publish()
if result.rc == mqtt.MQTT_ERR_SUCCESS:
    logging.info("Noise sentence published successfully")
else:
    logging.error(f"Failed to publish noise sentence: {result.rc}")

result = client.publish(topic, status_sentence)
result.wait_for_publish()
if result.rc == mqtt.MQTT_ERR_SUCCESS:
    logging.info("Status sentence published successfully")
else:
    logging.error(f"Failed to publish status sentence: {result.rc}")

# Print a confirmation
logging.info(f"Published messages to topic {topic}")

# Stop the loop and disconnect from the broker
client.loop_stop()
client.disconnect()
