import usb.core
import usb.util
import sys
import time
def send_command(command):
    endpoint_out = 0x02  # Command output endpoint
    command += '\r'  # Ensure the command ends with a carriage return
    try:
        dev.write(endpoint_out, command.encode('utf-8'))
        print(f'Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Error sending command "{command.strip()}": {e}')

VENDOR_ID = 0x0403
PRODUCT_ID = 0xf241

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print('Device not found')
    sys.exit(1)

if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
        print('Kernel driver detached')
    except usb.core.USBError as e:
        print(f'Could not detach kernel driver: {e}')
        sys.exit(1)

try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print(f'Could not set configuration: {e}')
    sys.exit(1)

try:
    usb.util.claim_interface(dev, 0)
    print('Interface claimed')
except usb.core.USBError as e:
    print(f'Could not claim interface: {e}')
    sys.exit(1)

# Send "RAW 1" command to enable raw data transmission
send_command("RAW 1")
"""
# Optionally send "RESET" command
user_input = input("Send RESET command? (y/n): ")
if user_input.lower() == 'y':"""
send_command("RESET")

try:
    endpoint = dev[0][(0,0)][0]
    while True:
        try:
            data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
            print('Data read from device:')
            print(data)
        except usb.core.USBError as e:
            print(f'Error reading data: {e}')
        time.sleep(1)  # Delay between reads
        
except KeyboardInterrupt:
    print('Interrupted by user')

finally:
    usb.util.release_interface(dev, 0)
    print('Interface released')
    try:
        dev.attach_kernel_driver(0)
        print('Kernel driver reattached')
    except usb.core.USBError as e:
        print(f'Could not reattach kernel driver: {e}')
