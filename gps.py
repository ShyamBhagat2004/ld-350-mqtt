import usb.core
import usb.util
import sys
import time
import threading

# Function to send a keep-alive command to the USB device.
def send_keep_alive(dev, endpoint_address):
    while True:
        try:
            dev.write(endpoint_address, b"\x4B\x41\x0A")  # Keep-alive packet.
            print("Keep alive command sent")
        except usb.core.USBError as e:
            print(f"Error sending keep alive command: {e}")
        time.sleep(1)  # Adjust the interval as needed.

# USB device identification and setup for GPS USB reader that outputs NMEA data.
VENDOR_ID = 0x1546
PRODUCT_ID = 0x01a7
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    print("GPS USB reader not found")
    sys.exit(1)

interface = 1  # Use the CDC Data interface as per lsusb output.
endpoint_in = 0x82  # Correct endpoint for reading data from lsusb.
endpoint_out = 0x01  # Endpoint for writing commands to the device (assumed for keep-alive).

# Detach any active kernel driver to claim the interface.
if dev.is_kernel_driver_active(interface):
    try:
        dev.detach_kernel_driver(interface)
        print("Kernel driver detached for interface", interface)
    except usb.core.USBError as e:
        print("Could not detach kernel driver for interface", interface, ":", e)
        sys.exit(1)

# Set USB device configuration.
try:
    dev.set_configuration()
    print("Device configuration set")
except usb.core.USBError as e:
    print("Could not set configuration:", e)
    sys.exit(1)

# Claim the USB interface.
try:
    usb.util.claim_interface(dev, interface)
    print("Interface", interface, "claimed")
except usb.core.USBError as e:
    print("Could not claim interface", interface, ":", e)
    sys.exit(1)

# Start a thread to send keep-alive packets to the device.
threading.Thread(target=send_keep_alive, args=(dev, endpoint_out), daemon=True).start()

# Main loop to read NMEA data from the GPS USB device.
try:
    while True:
        try:
            data = dev.read(endpoint_in, 512, timeout=5000)  # Reading larger chunks of data.
            nmea_output = ''.join([chr(x) for x in data])  # Directly convert bytes to ASCII string.
            print(nmea_output)  # Print the NMEA data to stdout.
        except usb.core.USBError as e:
            print("Error reading data from interface", interface, ":", e)
        time.sleep(0.01)  # Short delay to prevent high CPU usage.

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    # Clean up: release the USB interface and reattach any kernel drivers if needed.
    usb.util.release_interface(dev, interface)
    try:
        dev.attach_kernel_driver(interface)
        print("Kernel driver reattached for interface", interface)
    except usb.core.USBError as e:
        print("Could not reattach kernel driver for interface", interface, ":", e)
