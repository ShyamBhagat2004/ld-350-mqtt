import usb.core
import usb.util
import sys
import time
import csv

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

def parse_nmea_strikedata(sentence):
    try:
        if sentence.startswith('$WIMLI'):
            parts = sentence.split(',')
            ddd = parts[1]
            uuu = parts[2]
            bbb = parts[3].split('*')[0]
            return ['Strike', ddd, uuu, bbb]
        elif sentence.startswith('$WIMLN'):
            return ['Noise']
        elif sentence.startswith('$WIMSU'):
            parts = sentence.split(',')
            ccc = parts[1]
            sss = parts[2]
            ca = parts[3]
            sa = parts[4]
            ldns1 = parts[5]
            ldns2 = parts[6].split('*')[0]
            return ['Status', ccc, sss, ca, sa, ldns1, ldns2]
        else:
            return None
    except Exception as e:
        print(f'Error parsing NMEA sentence: {e}')
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

# Open CSV file for writing
csv_file = open('lightning_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Type', 'Corrected Distance', 'Uncorrected Distance', 'Bearing', 'Close Strike Rate', 'Total Strike Rate', 'Close Alarm', 'Severe Alarm', 'LDN1 State', 'LDN2 State'])

try:
    while True:
        for i in range(2):
            try:
                data = dev.read(endpoint_in[i], 64)  # Max packet size is 64 bytes
                print(f'Data read from interface {i}:')
                print(data)
                nmea_sentence = convert_to_nmea(data)
                if nmea_sentence:
                    parsed_data = parse_nmea_strikedata(nmea_sentence)
                    if parsed_data:
                        csv_writer.writerow(parsed_data)
                        print('Data written to CSV file')
            except usb.core.USBError as e:
                print(f'Interface {i}: Error reading data: {e}')
            time.sleep(0.1)

except KeyboardInterrupt:
    print('Interrupted by user')

finally:
    csv_file.close()  # Close the CSV file
    for i in range(2):
        usb.util.release_interface(dev, i)
        print(f'Interface {i} released')
        try:
            dev.attach_kernel_driver(i)
            print(f'Kernel driver reattached for interface {i}')
        except usb.core.USBError as e:
            print(f'Interface {i}: Could not reattach kernel driver: {e}')
