import re
import sqlite3

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
        "ID1": int(parts[1]),
        "ID2": int(parts[2]),
        "Data1": int(parts[3]),
        "Latitude": float(parts[4]),
        "Longitude": float(parts[5]),
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

def initialize_database():
    """Initialize the SQLite database and create table."""
    conn = sqlite3.connect('lightning_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS lightning_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            talker TEXT,
            id1 INTEGER,
            id2 INTEGER,
            data1 INTEGER,
            latitude REAL,
            longitude REAL
        )
    ''')
    conn.commit()
    conn.close()

def store_data(data):
    """Store parsed data in the SQLite database."""
    conn = sqlite3.connect('lightning_data.db')
    c = conn.cursor()

    for entry in data:
        c.execute('''
            INSERT INTO lightning_data (talker, id1, id2, data1, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (entry['Talker'], entry['ID1'], entry['ID2'], entry['Data1'], entry['Latitude'], entry['Longitude']))

    conn.commit()
    conn.close()

# Initialize the database
initialize_database()

# Parse the sample data
parsed_data = parse_nmea_data(sample_data)

# Store the parsed data in the database
store_data(parsed_data)

print("Data stored successfully.")
