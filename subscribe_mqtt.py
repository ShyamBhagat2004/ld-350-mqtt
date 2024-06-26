import paho.mqtt.client as mqtt

# Define the MQTT broker details
broker = "broker.emqx.io"
port = 8084
topic = "NMEA_Lightning"

# Callback when the client receives a message
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")

# Initialize MQTT client
client = mqtt.Client(client_id="mqttx_subscriber", clean_session=True, protocol=mqtt.MQTTv311)

# Assign the on_message callback
client.on_message = on_message

# Connect to the broker
client.connect(broker, port, 60)

# Subscribe to the topic
client.subscribe(topic)

# Start the loop to process received messages
client.loop_forever()
