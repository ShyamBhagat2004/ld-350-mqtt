import re

# Sample data - Replace this with your actual data source
sample_data = """
$LGT,12345,123456,12,34.5,56.7*6A
$LGT,12346,123457,13,34.6,56.8*6B
"""

# Regular expression to match NMEA style sentences
nmea_regex = re.compile(r'\$LGT,\d+,\d+,\d+,\d+\.\d+,\d+\.\d+\*[0-9A-F]{2}')

def parse_nmea_sentence(sentence):
    """Parse a single NMEA sentence."""
    if not nmea_regex.match(sentence):
        raise ValueError("Invalid NMEA sentence")

    # Split the sentence by commas and remove the starting $
    parts = sentence[1:].split(',')

    # Remove the checksum part after '*'
    checksum_index = parts[-1].find('*')
    if checksum_index != -1:
        parts[-1] = parts[-1][:checksum_index]

    return {
        "Talker": parts[0],
        "ID1": parts[1],
        "ID2": parts[2],
        "Data1": parts[3],
        "Latitude": parts[4],
        "Longitude": parts[5],
    }

def parse_nmea_data(data):
    """Parse NMEA data containing multiple sentences."""
    sentences = data.strip().split('\n')
    parsed_data = []

    for sentence in sentences:
        try:
            parsed_sentence = parse_nmea_sentence(sentence)
            parsed_data.append(parsed_sentence)
        except ValueError as e:
            print(f"Skipping invalid sentence: {sentence}. Error: {e}")

    return parsed_data

# Parse the sample data
parsed_data = parse_nmea_data(sample_data)

# Display the parsed data
for entry in parsed_data:
    print(entry)
