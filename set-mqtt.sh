#!/bin/bash

# Define variables
REPO_URL="https://github.com/ShyamBhagat2004/ld-350-mqtt.git"
DIR="/home/george/ld-350-mqtt"
LOG_FILE="/home/george/startup_script.log"

# Set the MQTT_TAG environment variable based on the device hostname
echo "Setting MQTT_TAG environment variable based on hostname" >> $LOG_FILE 2>&1
case "$(hostname)" in
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
echo "MQTT_TAG set to $MQTT_TAG" >> $LOG_FILE 2>&1
