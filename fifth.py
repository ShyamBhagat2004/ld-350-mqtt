import usb.core
import usb.util
import sys
import time

# Replace these with your device's Vendor ID and Product ID
VENDOR_ID = 0x0403
PRODUCT_ID = 0xf241

def find_device(vendor_id, product_id):
    dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
    if dev is None:
        print(f'Device not found. Vendor ID: {vendor_id}, Product ID: {product_id}')
        sys.exit(1)
    print('Device found')
    return dev

def detach_kernel_driver(dev, interface):
    if dev.is_kernel_driver_active(interface):
        try:
            dev.detach_kernel_driver(interface)
            print(f'Kernel driver detached from interface {interface}')
        except usb.core.USBError as e:
            print(f'Could not detach kernel driver from interface {interface}: {str(e)}')
            sys.exit(1)

def claim_interface(dev, interface):
    try:
        usb.util.claim_interface(dev, interface)
        print(f'Interface {interface} claimed')
    except usb.core.USBError as e:
        print(f'Could not claim interface {interface}: {str(e)}')
        sys.exit(1)

def release_interface(dev, interface):
    usb.util.release_interface(dev, interface)
    print(f'Interface {interface} released')

def reattach_kernel_driver(dev, interface):
    try:
        dev.attach_kernel_driver(interface)
        print(f'Kernel driver reattached to interface {interface}')
    except usb.core.USBError as e:
        print(f'Could not reattach kernel driver to interface {interface}: {str(e)}')

def send_command(dev, endpoint_out, command):
    try:
        dev.write(endpoint_out, command)
        print(f'Sent command: {command.decode()}')
    except usb.core.USBError as e:
        print(f'Error sending command {command.decode()}: {str(e)}')

# Main script
dev = find_device(VENDOR_ID, PRODUCT_ID)

# Detach kernel driver if necessary
detach_kernel_driver(dev, 0)
detach_kernel_driver(dev, 1)

# Set the active configuration
try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print(f'Could not set configuration: {str(e)}')
    sys.exit(1)

# Claim interfaces
claim_interface(dev, 0)
claim_interface(dev, 1)

# Select the correct endpoints for reading and writing
endpoint_in_0 = dev[0][(0, 0)][0].bEndpointAddress
endpoint_out_0 = dev[0][(0, 0)][1].bEndpointAddress
endpoint_in_1 = dev[0][(1, 0)][0].bEndpointAddress
endpoint_out_1 = dev[0][(1, 0)][1].bEndpointAddress

print(f'Endpoint IN for Interface 0: {endpoint_in_0}')
print(f'Endpoint OUT for Interface 0: {endpoint_out_0}')
print(f'Endpoint IN for Interface 1: {endpoint_in_1}')
print(f'Endpoint OUT for Interface 1: {endpoint_out_1}')

# Command to query raw data state
query_raw_command = b'RAW\r'

# Send command to query raw data state
send_command(dev, endpoint_out_0, query_raw_command)
time.sleep(1)  # Wait a bit to ensure the device processes the command

# Buffer to accumulate data
buffer = bytearray()

# Read the response
try:
    while True:
        try:
            print("Attempting to read data from Interface 0")
            data_0 = dev.read(endpoint_in_0, 512, timeout=1000)  # Increased buffer size
            print(f"Data from Interface 0: {data_0}")
            buffer.extend(data_0)
            
            print("Attempting to read data from Interface 1")
            data_1 = dev.read(endpoint_in_1, 512, timeout=1000)  # Increased buffer size
            print(f"Data from Interface 1: {data_1}")
            buffer.extend(data_1)
            
            # Print the accumulated buffer in hex format
            print('Data read from device (Interface 0 and Interface 1):')
            hex_data = ' '.join(f'{byte:02x}' for byte in buffer)
            print(hex_data)
            
            # For demonstration, print the buffer size and content as ASCII
            try:
                ascii_data = buffer.decode('ascii')
                print(f'Buffer as ASCII: {ascii_data}')
            except UnicodeDecodeError:
                print("Buffer contains non-ASCII characters.")
            
            # Check if the buffer contains the response for the raw data state
            if b'RAW' in buffer:
                print(f'Raw data state response: {ascii_data}')
                break
            
        except usb.core.USBError as e:
            if e.errno == 110:  # Timeout error
                continue
            print(f'Error reading data: {str(e)}')
            break
        time.sleep(1)
except KeyboardInterrupt:
    print('Interrupted by user')

# Release the interfaces
release_interface(dev, 0)
release_interface(dev, 1)

# Reattach the kernel driver
reattach_kernel_driver(dev, 0)
reattach_kernel_driver(dev, 1)
