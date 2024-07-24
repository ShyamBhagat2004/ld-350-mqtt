#!/bin/bash

# Variables
REPO_URL="https://github.com/ShyamBhagat2004/ld-350-mqtt.git"
DIR="/home/george/ld-350-mqtt"
REBOOT_SCRIPT_PATH="/home/george/reboot_script.sh"
USERNAME="george"

# Update and upgrade the system
echo "Updating and upgrading the system..."
sudo apt update && sudo apt upgrade -y

# Install necessary packages
echo "Installing necessary packages..."
sudo apt install -y python3 python3-venv python3-pip git

# Check if the directory exists and remove it if it does
if [ -d "$DIR" ]; then
  echo "Directory $DIR exists. Removing it."
  rm -rf "$DIR"
fi

# Clone the repository
echo "Cloning repository from $REPO_URL"
git clone "$REPO_URL" "$DIR"

# Navigate to the directory
cd "$DIR" || exit

# Create virtual environment
echo "Creating virtual environment 'venvpi' in $DIR"
python3 -m venv venvpi

# Activate virtual environment
echo "Activating virtual environment 'venvpi'"
source venvpi/bin/activate

# Install requirements
echo "Installing requirements from requirements.txt"
pip install -r requirements.txt

# Create the reboot script
echo "Creating the reboot script at $REBOOT_SCRIPT_PATH"
cat <<EOL > $REBOOT_SCRIPT_PATH
#!/bin/bash

# Set the MQTT_TAG environment variable based on the device hostname
case "\$(hostname)" in
    "rpi1")
        export MQTT_TAG="NMEA_Lightning_1"
        ;;
    "rpi2")
        export MQTT_TAG="NMEA_Lightning_2"
        ;;
    "rpi3")
        export MQTT_TAG="NMEA_Lightning_3"
        ;;
    *)
        export MQTT_TAG="NMEA_Lightning_Default"
        ;;
esac
echo "MQTT_TAG set to \$MQTT_TAG"

# Navigate to the project directory
cd $DIR

# Activate virtual environment
source venvpi/bin/activate

# Run main.py
python main.py
EOL

# Make the reboot script executable
chmod +x $REBOOT_SCRIPT_PATH

# Set up the reboot script to run at startup
echo "Setting up the reboot script to run at startup"
(crontab -l ; echo "@reboot $REBOOT_SCRIPT_PATH") | crontab -

echo "Setup is complete. Please reboot the Raspberry Pi to apply all changes."

