import usb.core
import usb.util
import sys

VENDOR_ID = 0x0403  # Replace with your Vendor ID
PRODUCT_ID = 0xf241  # Replace with your Product ID

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    print('Device not found')
    sys.exit(1)

# Detach kernel driver if necessary
if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
    except usb.core.USBError as e:
        print(f'Could not detach kernel driver: {str(e)}')
        sys.exit(1)

dev.set_configuration()
usb.util.claim_interface(dev, 0)

# Send command
command = b'RAW\r'
dev.write(1, command)

# Read response
response = dev.read(0x81, 64)
print('Response:', ''.join([chr(x) for x in response]))

usb.util.release_interface(dev, 0)
dev.attach_kernel_driver(0)
