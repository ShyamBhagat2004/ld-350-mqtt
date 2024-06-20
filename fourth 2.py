import usb.core
import usb.util
import sys
import csv
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
        print('Could not detach kernel driver: %s' % str(e))
        sys.exit(1)

# Set the active configuration
try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print('Could not set configuration: %s' % str(e))
    sys.exit(1)

# Claim interface 0
try:
    usb.util.claim_interface(dev, 0)
    print('Interface claimed')
except usb.core.USBError as e:
    print('Could not claim interface: %s' % str(e))
    sys.exit(1)

# Test different timings
timings = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1]  # Sleep intervals in seconds

for delay in timings:
    with open(f'usb_data_{delay}.csv', 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        endpoint = dev[0][(0,0)][0]
        start_time = time.time()
        end_time = start_time + 60  # Run each test for 60 seconds

        while time.time() < end_time:
            try:
                data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                csv_writer.writerow([time.time() - start_time, *data])
            except usb.core.USBError as e:
                csv_writer.writerow([time.time() - start_time, f'Error: {str(e)}'])
            time.sleep(delay)

# Release the interface
usb.util.release_interface(dev, 0)
print('Interface released')

# Reattach the kernel driver
try:
    dev.attach_kernel_driver(0)
    print('Kernel driver reattached')
except usb.core.USBError as e:
    print('Could not reattach kernel driver: %s' % str(e))
