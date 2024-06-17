import usb.core
import usb.util
import time

# Find the device (replace xxxx with your device's Vendor ID and Product ID)
VENDOR_ID = 0x0403  # Replace with your device's Vendor ID
PRODUCT_ID = 0xf241 # Replace with your device's Product ID

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    raise ValueError("Device not found")

# Detach kernel driver if necessary
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

# Set the active configuration
dev.set_configuration()

# Get endpoint instance
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

# Find the correct OUT and IN endpoints
out_endpoint = None
in_endpoint = None

for ep in intf:
    if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
        out_endpoint = ep.bEndpointAddress
    elif usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
        in_endpoint = ep.bEndpointAddress

if not out_endpoint or not in_endpoint:
    raise ValueError("Endpoints not found")

# Function to send commands to the device
def send_command(command):
    cmd = f"{command}\r".encode('ascii')
    print(f"Sending command: {cmd}")
    dev.write(out_endpoint, cmd)

# Initialize the device with captured commands
send_command("RAW1")
# Add other commands based on capture data if needed

# Function to read data from the device
def read_data(timeout=1000):
    try:
        data = dev.read(in_endpoint, 64, timeout=timeout)
        return data.tobytes().decode('ascii', errors='ignore').strip()
    except usb.core.USBError as e:
        if e.errno == 110:  # Timeout error
            return None
        else:
            raise

# Read and print the response
try:
    while True:
        response = read_data()
        if response:
            print(f"Received data: {response}")
except usb.core.USBError as e:
    print(f"USBError: {e}")
finally:
    # Release the device
    usb.util.release_interface(dev, intf)

print("Data collection complete.")
