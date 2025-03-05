import requests
import json
import sys
from datetime import datetime, timedelta

# API URL for hashprice data
API_URL = "https://insights.braiins.com/api/v1.0/hashrate-value-history?timeframe=all"

# Define month mappings
MONTH_MAPPING = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def fetch_data():
    """Fetches all historical hashprice data from Braiins API."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data.")
        sys.exit(1)

def find_nearest_date(data, target_date):
    """Finds the closest available hashprice date to target_date."""
    dates = [entry['x'] for entry in data]
    dates = sorted(dates, key=lambda x: abs(datetime.fromisoformat(x) - datetime.fromisoformat(target_date)))
    return dates[0]  # Return the closest available date

def calculate_fiat_revenue(mining_power, start_date, selected_months):
    """Calculates total fiat revenue (USD) from mining based on historical hashprice and selected months."""
    data = fetch_data()['hashrate_price']
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.today()
    total_revenue = 0.0

    # Convert selected months into a set of valid month numbers
    selected_month_numbers = {MONTH_MAPPING[month] for month in selected_months}

    current_date = start_date
    while current_date <= end_date:
        # **Exclude revenue from months not in the selected list**
        if current_date.month not in selected_month_numbers:
            current_date += timedelta(days=1)
            continue  # Skip this day

        closest_date = find_nearest_date(data, current_date.strftime("%Y-%m-%d"))

        # Get the hashprice for the closest available date
        for entry in data:
            if entry['x'] == closest_date:
                hashprice = entry['y']  # USD/TH/s/day
                daily_revenue = mining_power * hashprice  # Revenue for the day
                total_revenue += daily_revenue
                break

        current_date += timedelta(days=1)  # Move to the next day

    print(f"Total estimated fiat revenue (USD) from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}: ${total_revenue:.2f}")
    return total_revenue

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 calculate_monthly_fiat_rev.py <mining_power> <start_date YYYY-MM-DD> <Months Comma-Separated>")
        sys.exit(1)

    mining_power = float(sys.argv[1])  # Convert mining power to float (e.g., 10 TH/s)
    start_date = sys.argv[2]  # Start date input
    selected_months = sys.argv[3].split(",")  # Parse months input

    calculate_fiat_revenue(mining_power, start_date, selected_months)