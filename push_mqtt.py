import paho.mqtt.client as mqtt

# Define the MQTT broker details
broker = "broker.emqx.io"
port = 8084
topic = "NMEA_Lightning"

def calculate_checksum(nmea_sentence):
    """Calculate the NMEA checksum."""
    checksum = 0
    for char in nmea_sentence:
        checksum ^= ord(char)
    return checksum

def create_strike_sentence(raw_data):
    ddd = raw_data[0]  # Corrected strike distance
    uuu = raw_data[1]  # Uncorrected strike distance
    bbb_b = (raw_data[2] + raw_data[3] / 10.0)  # Bearing to strike

    nmea_sentence = f"WIMLI,{ddd},{uuu},{bbb_b:.1f}"
    checksum = calculate_checksum(nmea_sentence)
    full_sentence = f"${nmea_sentence}*{checksum:02X}\r\n"
    return full_sentence

def create_noise_sentence():
    nmea_sentence = "WIMLN"
    checksum = calculate_checksum(nmea_sentence)
    full_sentence = f"${nmea_sentence}*{checksum:02X}\r\n"
    return full_sentence

def create_status_sentence(raw_data):
    ccc = raw_data[0]  # Close strike rate
    sss = raw_data[1]  # Total strike rate
    ca = raw_data[2]   # Close alarm status
    sa = raw_data[3]   # Severe alarm status
    ldns1 = raw_data[4]  # Lightning network 1 connection state
    ldns2 = raw_data[5]  # Lightning network 2 connection state

    nmea_sentence = f"WIMSU,{ccc},{sss},{ca},{sa},{ldns1},{ldns2}"
    checksum = calculate_checksum(nmea_sentence)
    full_sentence = f"${nmea_sentence}*{checksum:02X}\r\n"
    return full_sentence

# Raw data arrays
arrays = [
    [49, 96, 73, 44, 50, 52, 50, 44, 51, 57, 52, 44, 48, 54, 52, 46, 49, 42, 53, 66, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 51, 44, 52, 49, 55, 44, 48, 49, 54, 46, 52, 42, 53, 57, 13, 10, 36, 87, 73, 77, 76, 78, 42, 65, 66, 13, 10, 36, 87, 73, 77, 76, 73],
    [49, 96, 44, 50, 50, 53, 44, 50, 49, 49, 44, 48, 56, 51, 46, 55, 42, 53, 55, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 51, 51, 52, 44, 51, 53, 51, 46, 48, 42, 53, 56, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 51, 52, 53, 44, 48, 49, 51],
    [49, 96, 46, 49, 42, 53, 52, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 50, 57, 51, 44, 48, 49, 55, 46, 50, 42, 53, 66, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 48, 56, 44, 50, 48, 48, 44, 48, 56, 50, 46, 54, 42, 53, 52, 13, 10, 36, 87, 73, 77, 76],
    [49, 96, 73, 44, 50, 51, 55, 44, 51, 54, 55, 44, 48, 50, 56, 46, 49, 42, 53, 70, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 48, 57, 44, 50, 48, 56, 44, 50, 54, 50, 46, 50, 42, 53, 57, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 52, 57, 44, 50, 54, 57, 44, 50, 56],
    [49, 96, 48, 46, 54, 42, 54, 56, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 52, 53, 57, 44, 50, 56, 51, 46, 49, 42, 54, 51, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 50, 55, 54, 44, 48, 53, 50, 46, 54, 42, 53, 70, 13, 10, 36, 87, 73, 77],
    [49, 96, 76, 73, 44, 50, 53, 51, 44, 50, 53, 50, 44, 51, 51, 57, 46, 54, 42, 54, 48, 13, 10, 36, 87, 73, 77, 76, 78, 42, 65, 66, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 48, 51, 44, 49, 55, 56, 44, 50, 57, 53, 46, 55, 42, 54, 52, 13, 10, 36, 87, 73, 77, 76],
    [49, 96, 73, 44, 50, 51, 48, 44, 50, 51, 56, 44, 48, 56, 53, 46, 57, 42, 54, 48, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 51, 57, 51, 44, 48, 49, 53, 46, 50, 42, 53, 65, 13, 10, 36, 87, 73, 77, 76, 78, 42, 65, 66, 13, 10, 36, 87, 73, 77, 76, 73],
    [49, 96, 44, 50, 51, 48, 44, 50, 49, 56, 44, 50, 56, 52, 46, 53, 42, 53, 66, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 52, 50, 44, 50, 54, 53, 44, 48, 50, 54, 46, 53, 42, 53, 65, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 48, 56, 44, 50, 57, 56, 44, 50, 57, 53],
    [49, 96, 46, 52, 42, 54, 57, 13, 10, 36, 87, 73, 77, 76, 73, 44, 49, 57, 48, 44, 49, 56, 48, 44, 50, 54, 49, 46, 57, 42, 53, 68, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 51, 49, 49, 44, 48, 48, 48, 46, 56, 42, 53, 48, 13, 10, 36, 87, 73, 77, 76],
    [49, 96, 73, 44, 50, 53, 52, 44, 51, 57, 51, 44, 48, 48, 48, 46, 48, 42, 53, 50, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 51, 50, 44, 50, 56, 55, 44, 50, 55, 50, 46, 48, 42, 53, 66, 13, 10, 36, 87, 73, 77, 76, 73, 44, 50, 53, 52, 44, 50, 56, 55, 44, 51, 48],
]

# Example function to determine the type of NMEA sentence to create
def process_data_array(data_array):
    if data_array[0] == 49 and data_array[1] == 96:  # Example condition to create a strike sentence
        return create_strike_sentence(data_array[2:6])
    elif data_array[0] == 49 and data_array[1] == 87:  # Example condition to create a status sentence
        return create_status_sentence(data_array[2:8])
    else:
        return create_noise_sentence()

# Initialize MQTT client
client = mqtt.Client(client_id="mqttx_bcb808ea", clean_session=True, protocol=mqtt.MQTTv311)
client.connect(broker, port, 60)

# Loop through each data array, convert to NMEA and publish
for data in arrays:
    nmea_sentence = process_data_array(data)
    client.publish(topic, nmea_sentence)
    print(f"Published: {nmea_sentence}")

# Disconnect the client after publishing all messages
client.disconnect()

