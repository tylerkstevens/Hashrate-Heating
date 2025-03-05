import requests
import json
import sys
from datetime import datetime

# API URL
API_URL = "https://insights.braiins.com/api/v1.0/hashrate-value-history?timeframe=all"

def fetch_data():
    """Fetches all historical hashrate data from Braiins API"""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data.")
        sys.exit(1)

def find_nearest_date(data, target_date):
    """Finds the nearest date with available hashvalue data."""
    dates = [entry['x'] for entry in data]
    dates = sorted(dates, key=lambda x: abs(datetime.fromisoformat(x) - datetime.fromisoformat(target_date)))
    
    return dates[0]  # Return the closest available date

def get_hashvalue(target_date):
    """Returns hashvalue for a given date or the closest available date."""
    data = fetch_data()['hashrate_value']  # <== FIXED THIS LINE

    # Check if exact date exists
    for entry in data:
        if entry['x'].startswith(target_date):
            print(f"Exact match found: {entry['x']} -> {entry['y']} sats/TH/s/day")
            return entry['y']

    # Find nearest available date if exact match is missing
    closest_date = find_nearest_date(data, target_date)
    for entry in data:
        if entry['x'] == closest_date:
            print(f"No exact match. Closest available date: {entry['x']} -> {entry['y']} sats/TH/s/day")
            return entry['y']

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 get_hashvalue.py YYYY-MM-DD")
        sys.exit(1)

    target_date = sys.argv[1]
    get_hashvalue(target_date)