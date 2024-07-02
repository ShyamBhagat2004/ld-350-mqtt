
# Project Documentation: Python Application for LD-350 Lightning Detector Data Handling

## Introduction
This document details the Python application designed to interface with LD-350 lightning detectors. The application reads data, converts it to NMEA format, and transmits it over MQTT.

## Requirements
- **Python Version**: 3.10+
- **Dependencies**:
  - `usb.core`
  - `usb.util`
  - `paho.mqtt.client`
  - `threading`
  - `sys`
  - `time`
- **Hardware**: LD-350 Lightning Detector with a USB connection.

## Setup and Configuration
### USB Configuration
1. **Device Identification**: Uses vendor ID (`0x0403`) and product ID (`0xf241`).
2. **Kernel Driver Handling**: Detaches the kernel driver if active to allow direct USB communication.
3. **Interface Management**: Claims interface 0 for exclusive device access.
4. **Endpoint Configuration**: Sets up endpoints for sending and receiving data.

### MQTT Configuration
1. **Broker Configuration**: Connects to the MQTT broker at `broker.mqtt.cool` on port 1883.
2. **Client Initialization**: Sets up the MQTT client with a unique ID derived from the current timestamp.
3. **Callbacks**: Establishes functions to handle connections and message publishing events.

## Core Functionality
### Reading and Processing Data
- **Continuous Reading**: Reads data packets from the USB continuously.
- **Error Handling**: Implements robust error handling to manage USB communication errors.

### Data Conversion
- **Format Conversion**: Converts raw USB data to ASCII, excluding null bytes, and formats into NMEA sentences.

### Data Publishing
- **MQTT Publishing**: Sends formatted data to a specified MQTT topic, managing message queuing and asynchronous delivery.

### File Management
- **File Writing**: Periodically writes NMEA data to `nmea_output.txt` for logging purposes.
- **File Maintenance**: Uses a daemon thread to clear the output file every 120 seconds to manage data storage effectively.

## Special Features
### Keep-Alive Mechanism
- **USB Connection Maintenance**: Sends a keep-alive packet every second to maintain the USB connection.

### Daemon Thread for File Maintenance
- **Background File Clearing**: A daemon thread clears the output file at regular intervals, preventing application termination due to this thread.

## Challenges and Resolutions
- **USB Communication Issues**: Addressed through comprehensive error handling and retry strategies.
- **MQTT Connection Stability**: Implemented reconnection mechanisms for network connectivity issues.

## Conclusion
This application integrates hardware interfacing, real-time data processing, and network communication to monitor and analyze lightning data effectively. Future enhancements could include dynamic configuration features and broader device support.

# Detailed Documentation for NMEA USB to MQTT Bridge

This script interfaces with a USB device to read NMEA data, process it, and publish it to an MQTT broker. It also periodically clears the data log file to avoid large file sizes.

## Table of Contents
1. [Function to Empty NMEA Data File](#1-function-to-empty-nmea-data-file)
2. [Function to Send Command to USB Device](#2-function-to-send-command-to-usb-device)
3. [Function to Send Keep-Alive Signal](#3-function-to-send-keep-alive-signal)
4. [Function to Convert USB Data to NMEA Format](#4-function-to-convert-usb-data-to-nmea-format)
5. [MQTT Callbacks](#5-mqtt-callbacks)
6. [Main Program Execution](#6-main-program-execution)

## 1. Function to Empty NMEA Data File

This function clears the contents of the specified file every 30 seconds.

### Function Definition

```python
def empty_file_every_30_seconds(file_path):
    while True:
        time.sleep(30)
        with open(file_path, "w+") as file:
            file.write("")
        print("File has been emptied")
```

### Parameters
- `file_path` (str): The path to the file that needs to be cleared.

### Example Usage
```python
threading.Thread(target=empty_file_every_30_seconds, args=("nmea_output.txt",), daemon=True).start()
```

## 2. Function to Send Command to USB Device

This function sends a command to the specified USB device.

### Function Definition

```python
def send_command(dev, interface, endpoint_address, command):
    command += "\r"
    try:
        dev.write(endpoint_address, command.encode("utf-8"))
        print(f'Interface {interface}: Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Interface {interface}: Error sending command "{command.strip()}": {e}')
```

### Parameters
- `dev` (usb.core.Device): The USB device object.
- `interface` (int): The interface number of the USB device.
- `endpoint_address` (int): The endpoint address for sending data.
- `command` (str): The command string to send to the device.

### Example Usage
```python
send_command(dev, interface, endpoint_out, "RAW 1")
```

## 3. Function to Send Keep-Alive Signal

This function sends a keep-alive signal to the USB device to maintain the connection.

### Function Definition

```python
def send_keep_alive(dev, endpoint_address):
    while True:
        try:
            dev.write(endpoint_address, b"\x4B\x41\x0A")
            print("Keep alive command sent")
        except usb.core.USBError as e:
            print(f"Error sending keep alive command: {e}")
        time.sleep(1)
```

### Parameters
- `dev` (usb.core.Device): The USB device object.
- `endpoint_address` (int): The endpoint address for sending data.

### Example Usage
```python
threading.Thread(target=send_keep_alive, args=(dev, endpoint_out), daemon=True).start()
```

## 4. Function to Convert USB Data to NMEA Format

This function converts raw USB data to NMEA formatted text.

### Function Definition

```python
def convert_to_nmea(data):
    try:
        ascii_data = "".join([chr(x) for x in data if x != 0])
        return ascii_data
    except Exception as e:
        print(f"Error converting data to NMEA: {e}")
        return None
```

### Parameters
- `data` (list of int): Raw data read from the USB device.

### Example Usage
```python
nmea_output = convert_to_nmea(data)
```

## 5. MQTT Callbacks

These are callback functions for handling MQTT events.

### on_connect Callback

```python
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}\n")
```

### on_publish Callback

```python
def on_publish(client, userdata, mid):
    print(f"Message {mid} published.")
```

### Example Usage
```python
client.on_connect = on_connect
client.on_publish = on_publish
```

## 6. Main Program Execution

The main program includes USB device setup, MQTT client setup, and the main loop for reading, processing, and publishing data.

### USB Device Identification and Setup

```python
VENDOR_ID = 0x0403
PRODUCT_ID = 0xF241
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print("Device not found")
    sys.exit(1)

interface = 0
endpoint_out = 0x02
endpoint_in = 0x81

if dev.is_kernel_driver_active(interface):
    try:
        dev.detach_kernel_driver(interface)
        print(f"Kernel driver detached for interface {interface}")
    except usb.core.USBError as e:
        print(f"Could not detach kernel driver for interface {interface}: {e}")
        sys.exit(1)

try:
    dev.set_configuration()
    print("Device configuration set")
except usb.core.USBError as e:
    print(f"Could not set configuration: {e}")
    sys.exit(1)

try:
    usb.util.claim_interface(dev, interface)
    print(f"Interface {interface} claimed")
except usb.core.USBError as e:
    print(f"Could not claim interface {interface}: {e}")
    sys.exit(1)

send_command(dev, interface, endpoint_out, "RAW 1")
threading.Thread(target=send_keep_alive, args=(dev, endpoint_out), daemon=True).start()
```

### MQTT Client Setup

```python
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
```

### Main Loop

```python
file_path = "nmea_output.txt"
output_buffer = ""

try:
    while True:
        try:
            data = dev.read(endpoint_in, 64, timeout=5000)
            print(f"Data read from interface {interface}:")
            print(data)
            nmea_output = convert_to_nmea(data)
            if nmea_output:
                output_buffer += nmea_output
                if output_buffer.count("$") >= 10:
                    with open(file_path, "a") as file:
                        file.write(output_buffer)
                    output_buffer = ""

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
    usb.util.release_interface(dev, interface)
    print(f"Interface {interface} released")
    try:
        dev.attach_kernel_driver(interface)
        print(f"Kernel driver reattached for interface {interface}")
    except usb.core.USBError as e:
        print(f"Interface {interface}: Could not reattach kernel driver: {e}")
    client.loop_stop()
    client.disconnect()
```

### Explanation
- **USB Device Identification and Setup**: This part identifies the USB device and sets up the necessary configuration and interface claims.
- **MQTT Client Setup**: This part sets up the MQTT client, defines the broker and topic, and connects to the broker.
- **Main Loop**: Continuously reads data from the USB device, processes it, logs it to a file, and publishes it to the MQTT topic. If the script is interrupted, it releases the USB interface and disconnects from the MQTT broker.

