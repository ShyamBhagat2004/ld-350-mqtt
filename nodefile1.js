const usb = require('usb');

// Constants
const VENDOR_ID = 0x0403;  // Example Vendor ID
const PRODUCT_ID = 0xf241; // Example Product ID
const READ_SIZE = 128;     // Adjust this buffer size to match your device's data packet size more closely

// Find the USB device
const device = usb.findByIds(VENDOR_ID, PRODUCT_ID);
if (!device) {
    console.log('Device not found');
    process.exit(1);
}

try {
    device.open();
    console.log('Device opened');

    // Access the first interface and claim it
    const interface = device.interfaces[0];
    interface.claim();

    // Find the first IN endpoint (assuming endpoint configuration is known and stable)
    const endpoint = interface.endpoints.find(ep => ep.direction === 'in');
    if (!endpoint) {
        throw new Error('Endpoint with direction "in" not found');
    }

    let readingCount = 0;
    const totalReadings = 200;

    // Function to handle data collection
    function collectData() {
        endpoint.transfer(READ_SIZE, (error, data) => {
            if (error) {
                console.error('Error reading:', error);
                // Optionally try to read again or handle error specifically
            } else {
                console.log(`Data read [${++readingCount}]:`, data);
            }

            if (readingCount < totalReadings) {
                collectData();  // Recursively collect next data
            } else {
                // Release the interface and close the device after all readings
                interface.release(true, (releaseError) => {
                    if (releaseError) {
                        console.error('Error releasing the interface:', releaseError);
                    }
                    device.close();
                    console.log('Device closed');
                });
            }
        });
    }

    collectData();
} catch (error) {
    console.error('Error:', error);
    if (device) {
        device.close();
        console.log('Device closed');
    }
}
