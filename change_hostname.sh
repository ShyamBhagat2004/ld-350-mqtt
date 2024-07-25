#!/bin/bash

# Function to change the hostname
change_hostname() {
  local new_hostname=$1

  # Update /etc/hostname
  echo "Changing hostname to $new_hostname..."
  echo $new_hostname | sudo tee /etc/hostname

  # Update /etc/hosts
  echo "Updating /etc/hosts..."
  sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$new_hostname/" /etc/hosts

  echo "Hostname changed to $new_hostname. A reboot is required to apply the changes."
}

# Prompt for the new hostname
echo -n "Enter the new hostname: "
read new_hostname

# Change the hostname
change_hostname $new_hostname

# Enable and restart the SSH service
echo "Ensuring SSH service is enabled..."
sudo systemctl enable ssh
sudo systemctl start ssh

echo "SSH service is enabled and running."

# Prompt to reboot
echo "Would you like to reboot now? (y/n)"
read reboot_now

if [ "$reboot_now" = "y" ]; then
  echo "Rebooting now..."
  sudo reboot
else
  echo "Please remember to reboot your Raspberry Pi later to apply the hostname change."
fi

