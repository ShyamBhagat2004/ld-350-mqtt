import usb.core
import usb.util
import sys
import time
import csv

def send_command(dev, endpoint_out, command):
    command += '\r'  # Ensure the command ends with a carriage return
    try:
        dev.write(endpoint_out, command.encode('utf-8'))
        print(f'Command "{command.strip()}" sent to endpoint {hex(endpoint_out)}')
    except usb.core.USBError as e:
        print(f'Error sending command "{command.strip()}": {e}')

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

def reset_device(dev, endpoint_out):
    reset_command = "RESET\r"
    try:
        dev.write(endpoint_out, reset_command.encode('utf-8'))
        print('Device reset command sent')
    except usb.core.USBError as e:
        print('Error sending reset command:', e)

VENDOR_ID = 0x0403
PRODUCT_ID = 0xf241

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if dev is None:
    print('Device not found')
    sys.exit(1)

# Detach kernel driver and set configuration
need_to_attach = False
if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
        need_to_attach = True
        print('Kernel driver detached')
    except usb.core.USBError as e:
        print('Could not detach kernel driver:', e)

try:
    dev.set_configuration()
    print('Device configuration set')
except usb.core.USBError as e:
    print('Could not set configuration:', e)

# Correct endpoints based on your device configuration
endpoint_out = 0x02  # This is an example; adjust as per actual device configuration
endpoint_in = 0x81  # This is an example; adjust as per actual device configuration

# Open CSV file for writing
csv_file = open('lightning_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Type', 'Corrected Distance', 'Uncorrected Distance', 'Bearing', 'Close Strike Rate', 'Total Strike Rate', 'Close Alarm', 'Severe Alarm', 'LDN1 State', 'LDN2 State'])

try:
    while True:
        send_command(dev, endpoint_out, "KA\r")  # Keep Alive command
        data = dev.read(endpoint_in, 64, timeout=5000)  # Max packet size is 64 bytes
        print('Data read from device:', data)
        nmea_sentence = convert_to_nmea(data)
        if nmea_sentence:
            parsed_data = parse_nmea_strikedata(nmea_sentence)
            if parsed_data:
                csv_writer.writerow(parsed_data)
                print('Data written to CSV file')

except KeyboardInterrupt:
    print('Interrupted by user')

finally:
    csv_file.close()  # Close the CSV file
    if need_to_attach:
        try:
            dev.attach_kernel_driver(0)
            print('Kernel driver reattached')
        except usb.core.USBError as e:
            print('Could not reattach kernel driver:', e)
