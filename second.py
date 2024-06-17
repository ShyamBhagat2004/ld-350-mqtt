import usb.core
import usb.util
import time
import csv

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

# Assuming the device has one IN endpoint
ep = usb.util.find_descriptor(
    intf,
    # match the first IN endpoint
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
)

assert ep is not None

# Initialize data storage
data_list = []
data_counter = {}

# Function to convert byte data to hex string
def bytes_to_hex(data):
    return ' '.join(f'{b:02x}' for b in data)

# Read data for 10 seconds
start_time = time.time()
try:
    while time.time() - start_time < 100:
        try:
            data = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize, timeout=1000)
            hex_data = bytes_to_hex(data)
            ascii_data = data.tobytes().decode('ascii', errors='ignore').strip()  # Decode bytes to ASCII string
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            if ascii_data:  # Check if data is not empty
                print(f"Hex data: {hex_data}")  # Debug print
                print(f"Received data: {ascii_data}")  # Debug print
                if ascii_data in data_counter:
                    data_counter[ascii_data] += 1
                else:
                    data_counter[ascii_data] = 1
                data_list.append([timestamp, ascii_data, data_counter[ascii_data]])
        except usb.core.USBError as e:
            print(f"USBError: {e}")
            continue
except KeyboardInterrupt:
    print("Exiting...")

# Release the device
usb.util.release_interface(dev, intf)

# Write data to a CSV file
with open('usb_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Timestamp", "Data", "Count"])  # Write header
    writer.writerows(data_list)

print("Data collection complete. Data written to usb_data.csv")
