# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install USB libraries
RUN apt-get update && apt-get install -y \
    libusb-1.0-0 \
    libusb-1.0-0-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Make port 1883 available to the world outside this container
EXPOSE 1883

# Run main.py when the container launches
CMD ["python", "seventh_two_current.py"]
