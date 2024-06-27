import usb.core
import usb.util
import sys
import time
import threading
import paho.mqtt.client as mqtt_client

def send_command(dev, interface, endpoint_address, command):
    command += '\r'  # Ensure the command ends with a carriage return
    try:
        dev.write(endpoint_address, command.encode('utf-8'))
        print(f'Interface {interface}: Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Interface {interface}: Error sending command "{command.strip()}": {e}')

def send_keep_alive(dev, endpoint_address):
    while True:
        try:
            dev.write(endpoint_address, b'\x4B\x41\x0A')
            print("Keep alive command sent")
        except usb.core.USBError as e:
            print(f'Error sending keep alive command: {e}')
        time.sleep(1)

def convert_to_nmea(data):
    try:
        ascii_data = ''.join([chr(x) for x in data if x != 0])  # Exclude null bytes
        return ascii_data
    except Exception as e:
        print(f'Error converting data to NMEA: {e}')
        return None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published.")

# MQTT settings
broker = "broker.mqtt.cool"
port = 1883
topic = "NMEA_Lightning"
client_id = f'python-mqtt-{int(time.time())}'

# Create MQTT client and set callbacks
client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311, transport="tcp")
client.on_connect = on_connect
client.on_publish = on_publish

# Connect to MQTT broker
try:
    client.connect(broker, port, 60)
    client.loop_start()  # Start loop to process callbacks
except Exception as e:
    print(f"Could not connect to MQTT broker: {e}")
    sys.exit(1)

VENDOR_ID = 0x0403
PRODUCT_ID = 0xf241

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print('Device not found')
    sys.exit(1)

interface = 0  # Only use the first interface
endpoint_out = 0x02
endpoint_in = 0x81

# Detach kernel driver and set configuration for the first interface
if dev.is_kernel_driver_active(interface):
    try:
        dev.detach_kernel_driver(interface)
        print(f'Kernel driver detached for interface {interface}')
    except usb.core.USBError as e:
        print(f'Could not detach kernel driver for interface {interface}: {e}')
        sys.exit(1)

try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print(f'Could not set configuration: {e}')
    sys.exit(1)

# Claim the first interface
try:
    usb.util.claim_interface(dev, interface)
    print(f'Interface {interface} claimed')
except usb.core.USBError as e:
    print(f'Could not claim interface {interface}: {e}')
    sys.exit(1)

# Send "RAW 1" command to the first interface
send_command(dev, interface, endpoint_out, "RAW 1")

# Start keep alive thread for the first interface
threading.Thread(target=send_keep_alive, args=(dev, endpoint_out), daemon=True).start()

try:
    while True:
        try:
            data = dev.read(endpoint_in, 64, timeout=5000)  # Max packet size is 64 bytes
            print(f'Data read from interface {interface}:')
            print(data)
            nmea_output = convert_to_nmea(data)
            if nmea_output:
                print('NMEA-style output:')
                print(nmea_output)
                # Publish to MQTT broker
                result = client.publish(topic, nmea_output)
                status = result[0]
                if status == 0:
                    print(f"Sent `{nmea_output}` to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic {topic}")
        except usb.core.USBError as e:
            print(f'Interface {interface}: Error reading data: {e}')
        time.sleep(0.2)

except KeyboardInterrupt:
    print('Interrupted by user')

finally:
    usb.util.release_interface(dev, interface)
    print(f'Interface {interface} released')
    try:
        dev.attach_kernel_driver(interface)
        print(f'Kernel driver reattached for interface {interface}')
    except usb.core.USBError as e:
        print(f'Interface {interface}: Could not reattach kernel driver: {e}')
    client.loop_stop()  # Stop MQTT loop
    client.disconnect()  # Disconnect from MQTT broker
