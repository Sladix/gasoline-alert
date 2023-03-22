import requests
import csv
from datetime import datetime
import time
import sys
import os
import simpleaudio as sa

API_URL = "https://data.economie.gouv.fr/api/records/1.0/search/"
DATASET = "prix-des-carburants-en-france-flux-instantane-v2"
DATA_FOLDER = "data"
BOLD = '\033[1m'
RESET = '\033[0m'

script_dir = os.path.dirname(os.path.abspath(__file__))
yena_file = os.path.join(script_dir, "yena.wav")
yenapu_file = os.path.join(script_dir, "yenapu.wav")

def get_gas_stations_data(postal_code, gas_type):
    params = {
        "dataset": DATASET,
        "facet": [
            "carburants_disponibles",
            "cp"
        ],
        "rows": 1000,
        "refine.cp": postal_code,
        "refine.carburants_disponibles": gas_type
    }
    response = requests.get(API_URL, params=params)
    return response.json()

def get_filename(file_prefix, gas_type):
    return f"{DATA_FOLDER}/{file_prefix}_{gas_type.lower()}_gas_availability_log.csv"

def load_last_known_state(filename):
    last_known_state = {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as csvfile:
            fieldnames = ["timestamp", "adresse", "availability"]
            reader = csv.DictReader(csvfile, fieldnames=fieldnames, delimiter=';', lineterminator='\n')
            for row in reader:
                if row and "adresse" in row:
                    address = row["adresse"]
                    last_known_state[address] = {
                        "availability": row["availability"] == "True",
                        "timestamp": row["timestamp"]
                    }
    return last_known_state


def play_wav_file(filename):
    wave_obj = sa.WaveObject.from_wave_file(filename)
    wave_obj.play()

def write_availability_to_file(filename, timestamp, adresse, availability):
    with open(filename, "a", encoding="utf-8") as csvfile:
        fieldnames = ["timestamp", "adresse", "availability"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";", lineterminator='\n')
        writer.writerow({"timestamp": timestamp, "adresse": adresse, "availability": availability})

def print_confidence_level(date):
    now = datetime.now()
    time_difference = now - date
    
    if time_difference.total_seconds() < 3600:
        confidence = "Very confident (less than an hour)"
        color = '\033[32m'
    elif 3600 <= time_difference.total_seconds() < 7200:
        confidence = "Confident (from 1 to 2 hours)"
        color = '\033[34m'
    elif 7200 <= time_difference.total_seconds() < 21600:
        confidence = "Unsure (from 2 to 6 hours)"
        color = '\033[33m'
    else:
        confidence = "Probably outdated (more than 6 hours)"
        color = '\033[31m'
    
    print(f"{color}{BOLD}{confidence}{RESET}")

def main(postal_code=None, gas_type=None, time_sleep=None):
    valid_gas_types = ["E10", "SP98", "SP95", "E85", "Gazole", "GPLc"]
    if gas_type not in valid_gas_types:
        print(f"Invalid gas type. Please choose from the following list: {', '.join(valid_gas_types)}")
        sys.exit(1)
    
    if postal_code is not None and not postal_code.isdigit():
        print("Invalid postal code. Please enter a numerical value.")
        sys.exit(1)

    file_prefix = postal_code if postal_code else "all"
    time_sleep = max(time_sleep, 60)
    filename = get_filename(file_prefix, gas_type)
    last_known_state = load_last_known_state(filename)
    first_run = True
    while True:
        data = get_gas_stations_data(postal_code, gas_type)
        records = data["records"]

        current_state = {}
        changed_count = 0
        latest_update = None
        latest_station = None

        has_available = False
        has_unavailable = False

        for record in records:
            address = record["fields"]["adresse"]
            availability = gas_type in record["fields"]["carburants_disponibles"].split(";")

            if first_run and availability:
                update_time = datetime.strptime(record["fields"][f"{gas_type.lower()}_maj"], "%Y-%m-%d %H:%M:%S")
                if latest_update is None or update_time > latest_update:
                    latest_update = update_time
                    latest_station = record

            current_state[address] = availability

            if address not in last_known_state or last_known_state[address]["availability"] != availability:
                if availability:
                    timestamp = record["fields"][f"{gas_type.lower()}_maj"]
                    print(f"{timestamp} : ALERT : {gas_type} is available at {record['fields']['adresse']}, {record['fields']['cp']} {record['fields']['ville']}")
                    has_available = True
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    has_unavailable = True
                write_availability_to_file(filename, timestamp, address, availability)
                changed_count += 1

        for address in last_known_state:
            if address not in current_state and last_known_state[address]["availability"] != False:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                write_availability_to_file(filename, timestamp, address, False)
                has_unavailable = True
                changed_count += 1

        if changed_count > 0:
            print(f"{changed_count} stations with changed availability.")
        if has_available:
            play_wav_file(yena_file)
        elif has_unavailable:
            play_wav_file(yenapu_file)

        last_known_state = {address: {"availability": availability} for address, availability in current_state.items()}

        if first_run and latest_station is not None:
            print_confidence_level(latest_update)
            print(f"{gas_type} is available at {latest_station['fields']['adresse']}, {latest_station['fields']['cp']} {latest_station['fields']['ville']} (Updated at: {latest_station['fields'][f'{gas_type.lower()}_maj']})")

        first_run = False

        time.sleep(time_sleep)  # Sleep for a specified interval


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gas_alert.py <gas_type> <postal_code> <interval>")
        sys.exit(1)
    GAS_TYPE = sys.argv[1]
    POSTAL_CODE = sys.argv[2] if len(sys.argv) > 2 else None
    TIME_SLEEP = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    main(POSTAL_CODE, GAS_TYPE, TIME_SLEEP)
