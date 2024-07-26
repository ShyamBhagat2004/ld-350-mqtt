#!/bin/bash

# Variables
REPO_URL="https://github.com/ShyamBhagat2004/ld-350-mqtt.git"
DIR="/home/george/ld-350-mqtt"
REBOOT_SCRIPT_PATH="/home/george/reboot_script.sh"
LOG_FILE="/home/george/startup_script.log"
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

# Define variables
REPO_URL="https://github.com/ShyamBhagat2004/ld-350-mqtt.git"
DIR="/home/george/ld-350-mqtt"
LOG_FILE="/home/george/startup_script.log"

# Start logging
echo "Script started at \$(date)" > \$LOG_FILE

# Log environment variables
echo "Environment variables:" >> \$LOG_FILE
env >> \$LOG_FILE

# Wait for network to be ready
echo "Waiting for network to be ready..." >> \$LOG_FILE 2>&1
sleep 60  # Wait for 60 seconds

# Check if the directory exists and remove it if it does
if [ -d "\$DIR" ]; then
  echo "Directory \$DIR exists. Removing it." >> \$LOG_FILE 2>&1
  rm -rf "\$DIR"
fi

# Clone the repository
echo "Cloning repository from \$REPO_URL" >> \$LOG_FILE 2>&1
if ! git clone "\$REPO_URL" "\$DIR" >> \$LOG_FILE 2>&1; then
  echo "Failed to clone repository. Exiting." >> \$LOG_FILE 2>&1
  exit 1
fi

# Navigate to the directory
cd "\$DIR" || exit

# Create virtual environment
echo "Creating virtual environment 'venvpi' in \$DIR" >> \$LOG_FILE 2>&1
python3 -m venv venvpi >> \$LOG_FILE 2>&1

# Activate virtual environment
echo "Activating virtual environment 'venvpi'" >> \$LOG_FILE 2>&1
source venvpi/bin/activate >> \$LOG_FILE 2>&1

# Install requirements
echo "Installing requirements from requirements.txt" >> \$LOG_FILE 2>&1
pip install -r requirements.txt >> \$LOG_FILE 2>&1

# Set the MQTT_TAG environment variable based on the device hostname
echo "Setting MQTT_TAG environment variable based on hostname" >> \$LOG_FILE 2>&1
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
        export MQTT_TAG="NMEA_Lightning"
        ;;
esac
echo "MQTT_TAG set to \$MQTT_TAG" >> \$LOG_FILE 2>&1

# Run main.py
echo "Running main.py" >> \$LOG_FILE 2>&1
python main.py >> \$LOG_FILE 2>&1

# End logging
echo "Script finished at \$(date)" >> \$LOG_FILE 2>&1
EOL

# Make the reboot script executable
chmod +x $REBOOT_SCRIPT_PATH

# Set up the reboot script to run at startup
echo "Setting up the reboot script to run at startup"
(crontab -l ; echo "@reboot $REBOOT_SCRIPT_PATH") | crontab -

echo "Setup is complete. Please reboot the Raspberry Pi to apply all changes."

