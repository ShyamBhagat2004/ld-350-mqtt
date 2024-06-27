import usb.core
import usb.util
import sys
import time

# Replace these with your device's Vendor ID and Product ID
VENDOR_ID = 0x0403
PRODUCT_ID = 0xf241

# Find the device
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print('Device not found')
    sys.exit(1)

# Detach kernel driver if necessary
if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
        print('Kernel driver detached')
    except usb.core.USBError as e:
        print(f'Could not detach kernel driver: {e}')
        sys.exit(1)

# Set the active configuration
try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print(f'Could not set configuration: {e}')
    sys.exit(1)

# Claim interface 0
try:
    usb.util.claim_interface(dev, 0)
    print('Interface claimed')
except usb.core.USBError as e:
    print(f'Could not claim interface: {e}')
    sys.exit(1)

def send_command(cmd, endpoint):
    """Send command to the USB device."""
    # Ensure the command ends with a carriage return
    cmd += '\r'
    # Convert string to bytes
    data = bytes(cmd, 'utf-8')
    try:
        dev.write(endpoint.bEndpointAddress, data, timeout=2000)
        print(f'Command sent: {cmd.strip()}')
    except usb.core.USBError as e:
        print(f'Error sending command: {e}')

def read_response(endpoint, timeout=2000):
    """Read response from the USB device."""
    try:
        data = dev.read(endpoint.bEndpointAddress, 333*endpoint.wMaxPacketSize, timeout)
        print('Response received:')
        print(data)
        return data
    except usb.core.USBError as e:
        print(f'Error reading response: {e}')

# Assume that the command sending endpoint is 1 and response reading endpoint is 0
command_endpoint = dev[0][(0,0)][1]
response_endpoint = dev[0][(0,0)][0]

# Send KA command to keep the USB connection alive
try:
    while True:
        send_command('KA', command_endpoint)
        read_response(response_endpoint)
        time.sleep(10)  # Adjust this sleep time as necessary
except KeyboardInterrupt:
    print('Interrupted by user')

# Release the interface
usb.util.release_interface(dev, 0)
print('Interface released')

# Reattach the kernel driver
try:
    dev.attach_kernel_driver(0)
    print('Kernel driver reattached')
except usb.core.USBError as e:
    print(f'Could not reattach kernel driver: {e}')
