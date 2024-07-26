import usb.core
import usb.util
import sys
import time
import threading
import paho.mqtt.client as mqtt_client
import os

# Function to empty the NMEA data file every 120 seconds for clean up and to avoid large, unwieldy files.
def empty_file_every_120_seconds(file_path):
    while True:
        time.sleep(120)
        with open(file_path, "w+") as file:
            file.write("")  
        print("File has been emptied")

# Utility function to send commands to the USB devices
def send_command(dev, interface, endpoint_address, command):
    command += "\r"
    try:
        dev.write(endpoint_address, command.encode("utf-8"))
        print(f'Interface {interface}: Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Interface {interface}: Error sending command "{command.strip()}": {e}')

# Function to continuously send a keep-alive signal to the device.
def send_keep_alive(dev, endpoint_address):
    while True:
        try:
            dev.write(endpoint_address, b"\x4B\x41\x0A")
            print("Keep alive command sent")
        except usb.core.USBError as e:
            print(f"Error sending keep alive command: {e}")
        time.sleep(1)

# Function to convert raw USB data to NMEA formatted text.
def convert_to_nmea(data):
    try:
        ascii_data = "".join([chr(x) for x in data if x != 0])
        return ascii_data
    except Exception as e:
        print(f"Error converting data to NMEA: {e}")
        return None

# MQTT callback handlers
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published.")

# Configuration settings for MQTT.
broker = "broker.mqtt.cool"
port = 1883
topic = os.getenv("MQTT_TAG", "NMEA_Lightning_Default").strip()  # Read the MQTT tag from environment variable
client_id = f"python-mqtt-{int(time.time())}"

# Debug print to confirm the topic
print(f"Using MQTT topic: {topic}")

client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311, transport="tcp")
client.on_connect = on_connect
client.on_publish = on_publish

try:
    client.connect(broker, port, 60)
    client.loop_start()
except Exception as e:
    print(f"Could not connect to MQTT broker: {e}")
    sys.exit(1)

# USB device setup for LD-350 Lightning Detector
ld_vendor_id = 0x0403
ld_product_id = 0xF241
ld_dev = usb.core.find(idVendor=ld_vendor_id, idProduct=ld_product_id)
if ld_dev is None:
    print("LD-350 device not found")
    sys.exit(1)

ld_interface = 0
ld_endpoint_out = 0x02
ld_endpoint_in = 0x81

# USB device setup for GPS USB reader
gps_vendor_id = 0x1546
gps_product_id = 0x01a7
gps_dev = usb.core.find(idVendor=gps_vendor_id, idProduct=gps_product_id)
if gps_dev is None:
    print("GPS USB reader not found")
    sys.exit(1)

gps_interface = 1
gps_endpoint_in = 0x82
gps_endpoint_out = 0x01

# Initialize the USB device configurations, claim interfaces, and detach kernel drivers
def initialize_usb_device(device, interface):
    if device.is_kernel_driver_active(interface):
        try:
            device.detach_kernel_driver(interface)
            print(f"Kernel driver detached for interface {interface}")
        except usb.core.USBError as e:
            print(f"Could not detach kernel driver for interface {interface}: {e}")
            sys.exit(1)
    try:
        device.set_configuration()
        usb.util.claim_interface(device, interface)
        print(f"Interface {interface} claimed")
    except usb.core.USBError as e:
        print(f"Error setting up device on interface {interface}: {e}")
        sys.exit(1)

initialize_usb_device(ld_dev, ld_interface)
initialize_usb_device(gps_dev, gps_interface)

# Start a thread to send keep-alive packets to the LD-350 device.
threading.Thread(target=send_keep_alive, args=(gps_dev, gps_endpoint_out), daemon=True).start()
threading.Thread(target=send_keep_alive, args=(ld_dev, ld_endpoint_out), daemon=True).start()
        
# Thread for emptying the file periodically
threading.Thread(target=empty_file_every_120_seconds, args=("nmea_output.txt",), daemon=True).start()

# Main loop to read data from both USB devices, merge them, and publish via MQTT.
try:
    while True:
        try:
            # Read data from LD-350
            ld_data = ld_dev.read(ld_endpoint_in, 64, timeout=5000)
            ld_output = convert_to_nmea(ld_data)
            
            # Read data from GPS
            gps_data = gps_dev.read(gps_endpoint_in, 512, timeout=5000)
            gps_output = ''.join([chr(x) for x in gps_data])
            
            # Combine data
            combined_data = f"{ld_output}\n{gps_output}"
            
            # Write combined data to file only if it starts with '$' and does not start with '$WIMLN*AB'
            lines = combined_data.split('\n')
            filtered_lines = [line for line in lines if line.startswith('$') and not line.startswith('$WIMLN*AB')]
            with open("nmea_output.txt", "a") as file:
                for line in filtered_lines:
                    file.write(line + "\n")
            
            # Publish combined data to MQTT
            filtered_combined_data = "\n".join(filtered_lines)
            client.publish(topic, filtered_combined_data)
            print(f"Published combined data to MQTT on topic {topic}: {filtered_combined_data}")
            
        except usb.core.USBError as e:
            print(f"USB Error: {e}")
        time.sleep(0.5)  # Adjust the sleep time to reduce the frequency of messages

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    usb.util.release_interface(ld_dev, ld_interface)
    usb.util.release_interface(gps_dev, gps_interface)
    try:
        ld_dev.attach_kernel_driver(ld_interface)
        gps_dev.attach_kernel_driver(gps_interface)
        print("Kernel drivers reattached for interfaces")
    except usb.core.USBError as e:
        print("Error reattaching kernel drivers:", e)
    client.loop_stop()
    client.disconnect()
