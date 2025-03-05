import requests
import json
import sys
from datetime import datetime, timedelta

# API URL for hashvalue (in sats/TH/s/day)
API_URL = "https://insights.braiins.com/api/v1.0/hashrate-value-history?timeframe=all"

def fetch_data():
    """Fetches all historical hashrate data from Braiins API"""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data.")
        sys.exit(1)

def get_closest_hashvalue(data, target_date):
    """Finds the closest available hashvalue for the given date."""
    hashvalue_data = data['hashrate_value']
    closest_entry = None
    min_diff = float('inf')
    
    for entry in hashvalue_data:
        entry_date = datetime.fromisoformat(entry['x'])
        diff = abs((entry_date - target_date).total_seconds())
        
        if diff < min_diff:
            min_diff = diff
            closest_entry = entry
    
    return closest_entry['y'] if closest_entry else None

def calculate_satoshi_revenue(mining_power, start_date):
    """Calculates the total satoshis mined over the specified period."""
    data = fetch_data()
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.today()
    
    total_satoshis = 0
    
    current_date = start_date
    while current_date <= end_date:
        hashvalue = get_closest_hashvalue(data, current_date)
        if hashvalue:
            daily_satoshis = mining_power * hashvalue
            total_satoshis += daily_satoshis
        
        current_date += timedelta(days=1)
    
    print(f"Total Satoshis Mined: {total_satoshis:.0f} sats")
    return total_satoshis

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 calculate_satoshi_revenue.py <mining_power> <start_date YYYY-MM-DD>")
        sys.exit(1)

    mining_power = float(sys.argv[1])
    start_date = sys.argv[2]
    
    calculate_satoshi_revenue(mining_power, start_date)
