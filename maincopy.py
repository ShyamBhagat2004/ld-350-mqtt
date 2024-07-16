import usb.core
import usb.util
import usb.backend.libusb1
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

# Function to detach the kernel driver if necessary
def detach_kernel_driver(dev, interface):
    if dev.is_kernel_driver_active(interface):
        try:
            dev.detach_kernel_driver(interface)
            print(f"Kernel driver detached for interface {interface}")
        except usb.core.USBError as e:
            print(f"Could not detach kernel driver for interface {interface}: {e}")
            return False
    return True

# Specify the backend
backend = usb.backend.libusb1.get_backend()

# Find the LD-350 Lightning Detector
dev_ld = usb.core.find(idVendor=0x0403, idProduct=0xf241, backend=backend)
if dev_ld is None:
    print("LD-350 Lightning Detector not found")
    sys.exit(1)

# Find the u-blox 7 GPS/GNSS Receiver
dev_gps = usb.core.find(idVendor=0x1546, idProduct=0x01a7, backend=backend)
if dev_gps is None:
    print("u-blox 7 GPS/GNSS Receiver not found")
    sys.exit(1)

# Handling LD-350 Lightning Detector
ld_interface_0 = 0
ld_interface_1 = 1
ld_endpoint_in = 0x83
ld_endpoint_out = 0x04

# Detach and claim interface 0 for LD-350
if not detach_kernel_driver(dev_ld, ld_interface_0):
    sys.exit(1)
try:
    usb.util.claim_interface(dev_ld, ld_interface_0)
    print("LD-350 Interface 0 claimed")
except usb.core.USBError as e:
    print(f"Could not claim LD-350 interface {ld_interface_0}: {e}")
    sys.exit(1)

# Detach and claim interface 1 for LD-350
if not detach_kernel_driver(dev_ld, ld_interface_1):
    sys.exit(1)
try:
    usb.util.claim_interface(dev_ld, ld_interface_1)
    print("LD-350 Interface 1 claimed")
except usb.core.USBError as e:
    print(f"Could not claim LD-350 interface {ld_interface_1}: {e}")
    sys.exit(1)

# Handling u-blox 7 GPS/GNSS Receiver
gps_interface_0 = 0
gps_interface_1 = 1
gps_endpoint_in = 0x82
gps_endpoint_out = 0x01

# Detach and claim interface 1 for GPS
if not detach_kernel_driver(dev_gps, gps_interface_1):
    sys.exit(1)
try:
    usb.util.claim_interface(dev_gps, gps_interface_1)
    print("GPS Interface 1 claimed")
except usb.core.USBError as e:
    print(f"Could not claim GPS interface {gps_interface_1}: {e}")
    sys.exit(1)

# Start a thread to send keep-alive packets to the LD-350 device.
threading.Thread(target=send_keep_alive, args=(dev_ld, ld_endpoint_out), daemon=True).start()

# Main loop to read NMEA data from the u-blox 7 GPS device.
try:
    while True:
        try:
            data = dev_gps.read(gps_endpoint_in, 512, timeout=5000)  # Reading larger chunks of data.
            nmea_output = ''.join([chr(x) for x in data])  # Directly convert bytes to ASCII string.
            print(nmea_output)  # Print the NMEA data to stdout.
        except usb.core.USBError as e:
            print("Error reading data from GPS interface", gps_interface_1, ":", e)
        time.sleep(0.01)  # Short delay to prevent high CPU usage.

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    # Clean up: release the USB interfaces and reattach any kernel drivers if needed.
    usb.util.release_interface(dev_ld, ld_interface_0)
    usb.util.release_interface(dev_ld, ld_interface_1)
    usb.util.release_interface(dev_gps, gps_interface_1)
    try:
        dev_ld.attach_kernel_driver(ld_interface_0)
        print("Kernel driver reattached for LD-350 interface", ld_interface_0)
    except usb.core.USBError as e:
        print("Could not reattach kernel driver for LD-350 interface", ld_interface_0, ":", e)
    try:
        dev_ld.attach_kernel_driver(ld_interface_1)
        print("Kernel driver reattached for LD-350 interface", ld_interface_1)
    except usb.core.USBError as e:
        print("Could not reattach kernel driver for LD-350 interface", ld_interface_1, ":", e)
    try:
        dev_gps.attach_kernel_driver(gps_interface_1)
        print("Kernel driver reattached for GPS interface", gps_interface_1)
    except usb.core.USBError as e:
        print("Could not reattach kernel driver for GPS interface", gps_interface_1, ":", e)
