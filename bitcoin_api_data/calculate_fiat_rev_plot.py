import requests
import json
import sys
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# API URL for hashprice (in USD/TH/s/day)
API_URL = "https://insights.braiins.com/api/v1.0/hashrate-value-history?timeframe=all"

def fetch_data():
    """Fetches all historical hashprice data from Braiins API."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data.")
        sys.exit(1)

def find_nearest_hashprice(data, target_date):
    """Finds the closest available hashprice for the given date."""
    hashprice_data = data['hashrate_price']
    closest_entry = None
    min_diff = float('inf')
    
    for entry in hashprice_data:
        entry_date = datetime.fromisoformat(entry['x'])
        diff = abs((entry_date - target_date).total_seconds())
        
        if diff < min_diff:
            min_diff = diff
            closest_entry = entry
    
    return closest_entry['y'] if closest_entry else None

def calculate_fiat_revenue(mining_power, start_date):
    """Calculates the total fiat revenue over the specified period and plots results."""
    data = fetch_data()
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.today()
    
    total_fiat_revenue = 0
    dates = []
    cumulative_fiat_revenue = []

    current_date = start_date
    while current_date <= end_date:
        hashprice = find_nearest_hashprice(data, current_date)
        if hashprice:
            daily_revenue = mining_power * hashprice  # USD revenue per day
            total_fiat_revenue += daily_revenue
        
        dates.append(current_date)
        cumulative_fiat_revenue.append(total_fiat_revenue)

        current_date += timedelta(days=1)

    print(f"Total Estimated Fiat Revenue: ${total_fiat_revenue:.2f}")

    # Plot results
    plt.figure(figsize=(10, 5))
    plt.plot(dates, cumulative_fiat_revenue, label="Cumulative Fiat Revenue (USD)", color="blue")
    plt.xlabel("Date")
    plt.ylabel("Total Revenue (USD)")
    plt.title(f"Cumulative Fiat Revenue ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})\nTotal: ${total_fiat_revenue:.2f}")
    plt.legend()
    plt.grid(True)
    plt.show()

    return total_fiat_revenue

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 calculate_fiat_rev_plot.py <mining_power> <start_date YYYY-MM-DD>")
        sys.exit(1)

    mining_power = float(sys.argv[1])
    start_date = sys.argv[2]
    
    calculate_fiat_revenue(mining_power, start_date)