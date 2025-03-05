import requests
import json
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from datetime import datetime, timedelta

# API URLs
HASHRATE_API_URL = "https://insights.braiins.com/api/v1.0/hashrate-value-history?timeframe=all"
BITCOIN_PRICE_API_URL = "https://insights.braiins.com/api/v1.0/price-stats"

# Define month mappings
MONTH_MAPPING = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def fetch_data(url):
    """Fetches data from the given API URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from {url}")
        sys.exit(1)

def find_nearest_date(data, target_date):
    """Finds the closest available date with hashprice and hashvalue data."""
    dates = [entry['x'] for entry in data]
    dates = sorted(dates, key=lambda x: abs(datetime.fromisoformat(x) - datetime.fromisoformat(target_date)))
    return dates[0]  # Return the closest available date

def calculate_revenue(mining_power, start_date, selected_months):
    """Calculates cumulative fiat revenue ($) and satoshi revenue over time, filtered by selected months."""
    data = fetch_data(HASHRATE_API_URL)
    hashprice_data = data['hashrate_price']
    hashvalue_data = data['hashrate_value']

    # Get today's Bitcoin price
    bitcoin_price_data = fetch_data(BITCOIN_PRICE_API_URL)
    bitcoin_price = bitcoin_price_data['price']  # USD per BTC

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.today()

    total_fiat_revenue = 0.0
    total_satoshis = 0
    dates = []
    fiat_revenue_over_time = []
    satoshi_revenue_over_time = []

    # Convert selected months into a set of valid month numbers
    selected_month_numbers = {MONTH_MAPPING[month] for month in selected_months}

    current_date = start_date
    while current_date <= end_date:
        # **Exclude revenue from months not in the selected list**
        if current_date.month not in selected_month_numbers:
            current_date += timedelta(days=1)
            continue  # Skip this day

        closest_date = find_nearest_date(hashprice_data, current_date.strftime("%Y-%m-%d"))

        # Get closest hashprice and hashvalue
        hashprice = None
        hashvalue = None

        for entry in hashprice_data:
            if entry['x'] == closest_date:
                hashprice = entry['y']
                break

        for entry in hashvalue_data:
            if entry['x'] == closest_date:
                hashvalue = entry['y']
                break

        if hashprice and hashvalue:
            daily_fiat_revenue = mining_power * hashprice  # USD Revenue for the day
            daily_satoshis = mining_power * hashvalue  # Satoshis mined per day
            
            total_fiat_revenue += daily_fiat_revenue
            total_satoshis += daily_satoshis

        dates.append(current_date)
        fiat_revenue_over_time.append(total_fiat_revenue)
        satoshi_revenue_over_time.append(total_satoshis)

        current_date += timedelta(days=1)  # Move to the next day

    # **Convert Total Satoshi Revenue to Fiat Equivalent using today's BTC price**
    total_sats_fiat_value = (total_satoshis / 100_000_000) * bitcoin_price

    print(f"Total Fiat Revenue (Selling Weekly): ${total_fiat_revenue:.2f}")
    print(f"Total Satoshis Mined (Held): {total_satoshis:,} sats (~${total_sats_fiat_value:.2f} at ${bitcoin_price:.2f}/BTC)")

    return dates, fiat_revenue_over_time, satoshi_revenue_over_time, total_fiat_revenue, total_satoshis, total_sats_fiat_value, bitcoin_price

def plot_revenue_comparison(dates, fiat_revenue, satoshi_revenue, total_fiat, total_sats, total_sats_fiat_value, bitcoin_price):
    """Plots fiat revenue ($) and satoshi revenue with dual Y-axes, ensuring the left Y-axis is scaled correctly."""
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # **Set the left Y-axis range to the larger of total fiat revenue or total sats fiat value**
    max_y_value = max(total_fiat, total_sats_fiat_value)
    ax1.set_ylim(0, total_sats_fiat_value * 1.1)  # Scale up by 10% to add margin

    # **Left Y-axis (Fiat Revenue in $)**
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Fiat Revenue ($)", color="blue")
    ax1.plot(dates, fiat_revenue, label="Cumulative Fiat Revenue ($)", color="blue", linewidth=2)
    ax1.tick_params(axis='y', labelcolor="blue")

    # **Right Y-axis (Total Satoshis Mined, NOT Scaled to Fiat)**
    ax2 = ax1.twinx()
    ax2.set_ylabel("Total Satoshis Mined", color="orange")
    ax2.set_ylim(0, total_sats * 1.1)  # Scale up by 10% to prevent cutoff
    ax2.plot(dates, satoshi_revenue, label="Cumulative Satoshi Revenue (sats)", color="orange", linewidth=2)
    ax2.tick_params(axis='y', labelcolor="orange")

    # **Format the right Y-axis for satoshi readability**
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,} sats"))  # Comma format for sats

    # **Update the title with the total satoshis mined**
    plt.title(
        f"Fiat vs. Satoshi Revenue Over Time\n"
        f"Fiat Savings (Sold Weekly): ${total_fiat:.2f} | "
        f"Total Satoshis Mined: {round(total_sats):,} sats | "
        f"Satoshi Value (Held): ${total_sats_fiat_value:.2f} at ${bitcoin_price:.2f}/BTC"
    )

    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 calculate_monthly_rev_plot.py <mining_power> <start_date YYYY-MM-DD> <Months Comma-Separated>")
        sys.exit(1)

    mining_power = float(sys.argv[1])
    start_date = sys.argv[2]
    selected_months = sys.argv[3].split(",")  # Parse months input

    dates, fiat_revenue, satoshi_revenue, total_fiat, total_sats, total_sats_fiat_value, bitcoin_price = calculate_revenue(mining_power, start_date, selected_months)
    plot_revenue_comparison(dates, fiat_revenue, satoshi_revenue, total_fiat, total_sats, total_sats_fiat_value, bitcoin_price)