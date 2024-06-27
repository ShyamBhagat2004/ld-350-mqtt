import usb.core
import usb.util
import sys
import time

def send_command(dev, interface, endpoint_address, command):
    command += '\r'  # Ensure the command ends with a carriage return
    try:
        dev.write(endpoint_address, command.encode('utf-8'))
        print(f'Interface {interface}: Command "{command.strip()}" sent')
    except usb.core.USBError as e:
        print(f'Interface {interface}: Error sending command "{command.strip()}": {e}')

def convert_to_nmea(data):
    try:
        ascii_data = ''.join([chr(x) for x in data if x != 0])  # Exclude null bytes
        return ascii_data
    except Exception as e:
        print(f'Error converting data to NMEA: {e}')
        return None

VENDOR_ID = 0x0403
PRODUCT_ID = 0xf241

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print('Device not found')
    sys.exit(1)

# Detach kernel driver and set configuration for both interfaces
for i in range(2):  # Assuming two interfaces
    if dev.is_kernel_driver_active(i):
        try:
            dev.detach_kernel_driver(i)
            print(f'Kernel driver detached for interface {i}')
        except usb.core.USBError as e:
            print(f'Could not detach kernel driver for interface {i}: {e}')
            sys.exit(1)

try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print(f'Could not set configuration: {e}')
    sys.exit(1)

# Define endpoints based on your device configuration
endpoint_out = {0: 0x02, 1: 0x04}
endpoint_in = {0: 0x81, 1: 0x83}

# Claim both interfaces
for i in range(2):
    try:
        usb.util.claim_interface(dev, i)
        print(f'Interface {i} claimed')
    except usb.core.USBError as e:
        print(f'Could not claim interface {i}: {e}')
        sys.exit(1)

# Send "RAW 1" command to both interfaces
for i in range(2):
    send_command(dev, i, endpoint_out[i], "RAW 1")

# Optionally send "RESET" command to both interfaces
user_input = input("Send RESET command? (y/n): ")
if user_input.lower() == 'y':
    for i in range(2):
        send_command(dev, i, endpoint_out[i], "RESET")

try:
    while True:
        for i in range(2):
            try:
                data = dev.read(endpoint_in[i], 64)  # Max packet size is 64 bytes
                print(f'Data read from interface {i}:')
                print(data)
                nmea_output = convert_to_nmea(data)
                if nmea_output:
                    print('NMEA-style output:')
                    print(nmea_output)
            except usb.core.USBError as e:
                print(f'Interface {i}: Error reading data: {e}')
            time.sleep(0.1)

except KeyboardInterrupt:
    print('Interrupted by user')

finally:
    for i in range(2):
        usb.util.release_interface(dev, i)
        print(f'Interface {i} released')
        try:
            dev.attach_kernel_driver(i)
            print(f'Kernel driver reattached for interface {i}')
        except usb.core.USBError as e:
            print(f'Interface {i}: Could not reattach kernel driver: {e}')
