import requests
import json
import sys
from datetime import datetime, timedelta

# API URL for hashvalue (in sats/TH/s/day)
API_URL = "https://insights.braiins.com/api/v1.0/hashrate-value-history?timeframe=all"

# Define seasonal month mappings
SEASONAL_MONTHS = {
    "Jan-Mar": [1, 2, 3],
    "Apr-Jun": [4, 5, 6],
    "Jul-Sep": [7, 8, 9],
    "Oct-Dec": [10, 11, 12]
}

def fetch_data():
    """Fetches all historical hashvalue data from Braiins API."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data.")
        sys.exit(1)

def find_nearest_date(data, target_date):
    """Finds the closest available hashvalue date to target_date."""
    dates = [entry['x'] for entry in data]
    dates = sorted(dates, key=lambda x: abs(datetime.fromisoformat(x) - datetime.fromisoformat(target_date)))
    return dates[0]  # Return the closest available date

def calculate_satoshi_revenue(mining_power, start_date, selected_seasons):
    """Calculates total satoshi revenue based on historical hashvalue and selected seasons."""
    data = fetch_data()['hashrate_value']
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.today()
    total_satoshis = 0

    # Convert selected seasons into a set of valid months
    selected_months = set()
    for season in selected_seasons:
        selected_months.update(SEASONAL_MONTHS[season])

    current_date = start_date
    while current_date <= end_date:
        # **Exclude revenue from months not in the selected seasons**
        if current_date.month not in selected_months:
            current_date += timedelta(days=1)
            continue  # Skip this day
        
        closest_date = find_nearest_date(data, current_date.strftime("%Y-%m-%d"))

        # Get the hashvalue for the closest available date
        for entry in data:
            if entry['x'] == closest_date:
                hashvalue = entry['y']  # Sats/TH/s/day
                daily_satoshis = mining_power * hashvalue  # Satoshis for the day
                total_satoshis += daily_satoshis
                break
        
        current_date += timedelta(days=1)  # Move to the next day

    print(f"Total estimated satoshi revenue from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}: {total_satoshis:.0f} sats")
    return total_satoshis

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 calculate_seasonal_satoshi_rev.py <mining_power> <start_date YYYY-MM-DD> <Seasons Comma-Separated>")
        sys.exit(1)

    mining_power = float(sys.argv[1])  # Convert mining power to float (e.g., 10 TH/s)
    start_date = sys.argv[2]  # Start date input
    selected_seasons = sys.argv[3].split(",")  # Parse seasons input

    calculate_satoshi_revenue(mining_power, start_date, selected_seasons)