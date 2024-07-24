import usb.core
import usb.util
import sys
import time
import threading
import paho.mqtt.client as mqtt_client
import math

# Function to empty the NMEA data file every 120 seconds for clean up and to avoid large, unwieldy files.
def empty_file_every_120_seconds(file_path):
    while True:
        time.sleep(120)
        with open(file_path, "w+") as file:
            file.write("")  
        print("File has been emptied")

# Utility function to send commands to the USB devices
def send_command(dev, endpoint_address, command):
    command += "\r"
    try:
        dev.write(endpoint_address, command.encode("utf-8"))
        print(f'Device {dev}: Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Device {dev}: Error sending command "{command.strip()}": {e}')

# Function to continuously send a keep-alive signal to the device.
def send_keep_alive(dev, endpoint_address):
    while True:
        try:
            dev.write(endpoint_address, b"\x4B\x41\x0A")
            print(f"Keep alive command sent to {dev}")
        except usb.core.USBError as e:
            print(f"Error sending keep alive command to {dev}: {e}")
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
topic = "NMEA_Lightning"
client_id = f"python-mqtt-{int(time.time())}"

client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311, transport="tcp")
client.on_connect = on_connect
client.on_publish = on_publish

try:
    client.connect(broker, port, 60)
    client.loop_start()
except Exception as e:
    print(f"Could not connect to MQTT broker: {e}")
    sys.exit(1)

# USB device setup for LD-350 Lightning Detectors
ld_vendor_id = 0x0403
ld_product_id = 0xF241
ld_devices = usb.core.find(find_all=True, idVendor=ld_vendor_id, idProduct=ld_product_id)
ld_devices = list(ld_devices)  # Convert to list

if not ld_devices:
    print("No LD-350 devices found")
    sys.exit(1)

print(f"Found {len(ld_devices)} LD-350 devices")

# Function to initialize the USB device, find and claim its interface, and find the endpoints
def initialize_usb_device(device):
    if device.is_kernel_driver_active(0):
        try:
            device.detach_kernel_driver(0)
            print(f"Kernel driver detached for device {device}")
        except usb.core.USBError as e:
            print(f"Could not detach kernel driver for device {device}: {e}")
            sys.exit(1)

    try:
        device.set_configuration()
        usb.util.claim_interface(device, 0)
        print(f"Interface claimed for device {device}")
    except usb.core.USBError as e:
        print(f"Error setting up device {device}: {e}")
        sys.exit(1)

    cfg = device.get_active_configuration()
    intf = cfg[(0, 0)]

    out_endpoint = None
    in_endpoint = None

    for ep in intf:
        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
            out_endpoint = ep
        elif usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
            in_endpoint = ep

    if not out_endpoint or not in_endpoint:
        print(f"Could not find endpoints for device {device}")
        sys.exit(1)

    return out_endpoint, in_endpoint

ld_endpoints = [initialize_usb_device(ld_dev) for ld_dev in ld_devices]

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

def initialize_usb_device_gps(device, interface):
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
        print(f"Interface {interface} claimed for GPS device")
    except usb.core.USBError as e:
        print(f"Error setting up GPS device on interface {interface}: {e}")
        sys.exit(1)

initialize_usb_device_gps(gps_dev, gps_interface)

# Start threads to send keep-alive packets to the LD-350 devices.
for ld_dev, (ld_endpoint_out, _) in zip(ld_devices, ld_endpoints):
    threading.Thread(target=send_keep_alive, args=(ld_dev, ld_endpoint_out), daemon=True).start()

threading.Thread(target=send_keep_alive, args=(gps_dev, gps_endpoint_out), daemon=True).start()

# Thread for emptying the file periodically
threading.Thread(target=empty_file_every_120_seconds, args=("nmea_output.txt",), daemon=True).start()

# Function to perform triangulation
def triangulate(ld_data_list):
    # This function should implement the triangulation algorithm
    # For simplicity, let's assume it returns the (x, y) position of the lightning strike
    # You will need to implement the actual triangulation logic based on time differences and distances
    x = 0.0
    y = 0.0
    # Add your triangulation logic here
    return x, y

# Function to read data from a device
def read_data_from_device(device, endpoint_in):
    try:
        data = device.read(endpoint_in.bEndpointAddress, endpoint_in.wMaxPacketSize, timeout=5000)
        return convert_to_nmea(data)
    except usb.core.USBError as e:
        print(f"USB Error reading from device {device}: {e}")
        return None

# Main loop to read data from all USB devices, merge them, and publish via MQTT.
try:
    while True:
        try:
            ld_outputs = []
            threads = []

            # Create threads to read data from each LD-350 device
            for ld_dev, (_, ld_endpoint_in) in zip(ld_devices, ld_endpoints):
                thread = threading.Thread(target=lambda q, d, e: q.append(read_data_from_device(d, e)), args=(ld_outputs, ld_dev, ld_endpoint_in))
                threads.append(thread)
                thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()

            # Perform triangulation
            x, y = triangulate(ld_outputs)

            # Read data from GPS
            gps_data = gps_dev.read(gps_endpoint_in, 512, timeout=5000)
            gps_output = ''.join([chr(x) for x in gps_data])

            # Combine data
            combined_data = f"Triangulated Position: ({x}, {y})\n"
            combined_data += "\n".join(ld_outputs)
            combined_data += f"\n{gps_output}"

            # Write combined data to file only if it starts with '$' and does not start with '$WIMLN*AB'
            lines = combined_data.split('\n')
            filtered_lines = [line for line in lines if line.startswith('$') and not line.startswith('$WIMLN*AB')]
            with open("nmea_output.txt", "a") as file:
                for line in filtered_lines:
                    file.write(line + "\n")

            # Publish combined data to MQTT
            filtered_combined_data = "\n".join(filtered_lines)
            client.publish(topic, filtered_combined_data)
            print(f"Published combined data to MQTT: {filtered_combined_data}")

        except usb.core.USBError as e:
            print(f"USB Error: {e}")
        time.sleep(0.5)  # Adjust the sleep time to reduce the frequency of messages

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    for ld_dev in ld_devices:
        usb.util.release_interface(ld_dev, 0)
        try:
            ld_dev.attach_kernel_driver(0)
            print(f"Kernel driver reattached for device {ld_dev}")
        except usb.core.USBError as e:
            print("Error reattaching kernel drivers:", e)

    usb.util.release_interface(gps_dev, gps_interface)
    try:
        gps_dev.attach_kernel_driver(gps_interface)
        print("Kernel driver reattached for GPS interface")
    except usb.core.USBError as e:
        print("Error reattaching kernel drivers:", e)

    client.loop_stop()
    client.disconnect()
