import usb.core
import usb.util
import sys
import time
import threading
import paho.mqtt.client as mqtt_client

# Function to empty the NMEA data file every 30 seconds for clean up and to avoid large, unwieldy files.
def empty_file_every_120_seconds(file_path):
    while True:
        time.sleep(30)  # Interval set to 30 seconds.
        with open(file_path, "w+") as file:
            file.write("")  # Clear the contents of the file.
        print("File has been emptied")


# Starting a background thread that runs the above function. It runs as a daemon so it won't prevent the program from exiting.
threading.Thread(
    target=empty_file_every_120_seconds, args=("nmea_output.txt",), daemon=True
).start()

# Function to send a command to the USB device.
def send_command(dev, interface, endpoint_address, command):
    command += "\r"  # Append carriage return to ensure proper command termination.
    try:
        dev.write(endpoint_address, command.encode("utf-8"))
        print(f'Interface {interface}: Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Interface {interface}: Error sending command "{command.strip()}": {e}')


# Function to continuously send a keep-alive signal to the device to maintain the connection.
def send_keep_alive(dev, endpoint_address):
    while True:
        try:
            dev.write(endpoint_address, b"\x4B\x41\x0A")  # Keep-alive packet.
            print("Keep alive command sent")
        except usb.core.USBError as e:
            print(f"Error sending keep alive command: {e}")
        time.sleep(1)


# Function to convert raw USB data to NMEA formatted text.
def convert_to_nmea(data):
    try:
        ascii_data = "".join(
            [chr(x) for x in data if x != 0]
        )  # Convert to ASCII and exclude null bytes.
        return ascii_data
    except Exception as e:
        print(f"Error converting data to NMEA: {e}")
        return None


# MQTT callback for successful connection.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}\n")


# MQTT callback for when a message is published.
def on_publish(client, userdata, mid):
    print(f"Message {mid} published.")


# Configuration settings for MQTT.
broker = "broker.mqtt.cool"
port = 1883
topic = "NMEA_Lightning"
client_id = f"python-mqtt-{int(time.time())}"

# Set up MQTT client and define callback handlers.
client = mqtt_client.Client(
    client_id=client_id, protocol=mqtt_client.MQTTv311, transport="tcp"
)
client.on_connect = on_connect
client.on_publish = on_publish

# Attempt to connect to the MQTT broker.
try:
    client.connect(broker, port, 60)
    client.loop_start()  # Start the network loop in a separate thread for handling MQTT communication.
except Exception as e:
    print(f"Could not connect to MQTT broker: {e}")
    sys.exit(1)

# USB device identification and setup.
VENDOR_ID = 0x0403
PRODUCT_ID = 0xF241
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print("Device not found")
    sys.exit(1)

interface = 0  # Use the first interface.
endpoint_out = 0x02
endpoint_in = 0x81

# Detach any active kernel driver to claim the interface.
if dev.is_kernel_driver_active(interface):
    try:
        dev.detach_kernel_driver(interface)
        print(f"Kernel driver detached for interface {interface}")
    except usb.core.USBError as e:
        print(f"Could not detach kernel driver for interface {interface}: {e}")
        sys.exit(1)

# Set USB device configuration.
try:
    dev.set_configuration()
    print("Device configuration set")
except usb.core.USBError as e:
    print(f"Could not set configuration: {e}")
    sys.exit(1)

# Claim the USB interface.
try:
    usb.util.claim_interface(dev, interface)
    print(f"Interface {interface} claimed")
except usb.core.USBError as e:
    print(f"Could not claim interface {interface}: {e}")
    sys.exit(1)

# Send the initial command to the USB device to start data transmission.
send_command(dev, interface, endpoint_out, "RAW 1")

# Start a thread to send keep-alive packets to the device.
threading.Thread(target=send_keep_alive, args=(dev, endpoint_out), daemon=True).start()

# Initialize the file for data logging.
file_path = "nmea_output.txt"
output_buffer = ""

# Main loop to read data from the USB device, convert it, and publish via MQTT.
try:
    while True:
        try:
            data = dev.read(endpoint_in, 64, timeout=5000)  # Read data from the device.
            print(f"Data read from interface {interface}:")
            print(data)
            nmea_output = convert_to_nmea(data)
            if nmea_output:
                output_buffer += nmea_output  # Append converted data to the buffer.
                if (
                    output_buffer.count("$") >= 10
                ):  # Check if buffer has enough data to log.
                    with open(file_path, "a") as file:
                        file.write(output_buffer)  # Write data to file.
                    output_buffer = ""  # Clear buffer.

                # Publish data to MQTT topic.
                start = 0
                while True:
                    start_idx = output_buffer.find("$", start)
                    end_idx = output_buffer.find("$", start_idx + 1)
                    if start_idx != -1 and end_idx != -1:
                        message = output_buffer[start_idx:end_idx]
                        client.publish(topic, message)
                        start = end_idx
                    else:
                        break
        except usb.core.USBError as e:
            print(f"Interface {interface}: Error reading data: {e}")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    # Clean up: release the USB interface and reattach any kernel drivers if needed.
    usb.util.release_interface(dev, interface)
    print(f"Interface {interface} released")
    try:
        dev.attach_kernel_driver(interface)
        print(f"Kernel driver reattached for interface {interface}")
    except usb.core.USBError as e:
        print(f"Interface {interface}: Could not reattach kernel driver: {e}")
    client.loop_stop()  # Stop the MQTT client's network loop.
    client.disconnect()  # Disconnect from the MQTT broker.
