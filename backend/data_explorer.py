import os
import json
import pandas as pd
from datetime import datetime, timezone
import warnings

# Ignore warnings from pandas about timezone conversion, which are expected here
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- Configuration ---
LOG_DIRECTORY = "logs"
SERVICE_NAMES = ["auth-service", "order-service", "product-service"]

def load_all_logs_into_dataframe():
    """Reads all logs from all files and loads them into a single pandas DataFrame."""
    all_log_data = []
    
    for service_name in SERVICE_NAMES:
        log_file_path = os.path.join(LOG_DIRECTORY, f"{service_name}.log")
        if not os.path.exists(log_file_path):
            continue
            
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    # We extract the flat JSON details we care about
                    flat_log = log_entry["record"]["extra"]["json"]
                    
                    # Also grab the timestamp
                    log_time_str = log_entry["record"]["time"]["repr"]
                    flat_log['timestamp'] = pd.to_datetime(log_time_str).tz_convert('UTC')
                    
                    all_log_data.append(flat_log)
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue

    if not all_log_data:
        return pd.DataFrame() # Return empty DataFrame if no logs found
        
    return pd.DataFrame(all_log_data)

def run_analysis(df):
    """Performs and prints several data analyses using pandas."""
    if df.empty:
        print("No data found in logs. Please ensure services and controller are running.")
        return

    print("\n" + "="*50)
    print(" Traditional Data Analysis Report")
    print("="*50 + "\n")

    # --- Insight 1: Overall Service Performance ---
    print("--- 1. Overall Service Performance ---")
    performance_summary = df.groupby('service').agg(
        total_requests=('service', 'count'),
        avg_response_time_ms=('process_time_ms', 'mean'),
        avg_cpu_percent=('cpu_usage_percent', 'mean'),
        error_rate=('status_code', lambda x: (x >= 400).mean() * 100)
    ).round(2)
    print(performance_summary)
    print("\n* Insight: This table shows which service is the busiest, the slowest, and the most error-prone.\n")

    # --- Insight 2: Busiest Time Period ---
    print("--- 2. Busiest Time Period (by minute) ---")
    # Set the timestamp as the index for time-based operations
    df_time_indexed = df.set_index('timestamp')
    requests_per_minute = df_time_indexed.resample('1min').size()
    busiest_minute = requests_per_minute.idxmax()
    request_count = requests_per_minute.max()
    print(f"The busiest minute was {busiest_minute.strftime('%Y-%m-%d %H:%M:%S')} UTC with {request_count} requests.\n")
    
    # --- Insight 3: Correlation between CPU/Memory and Response Time ---
    print("--- 3. Correlation Analysis ---")
    correlation_matrix = df[['process_time_ms', 'cpu_usage_percent', 'memory_usage_percent']].corr()
    print(correlation_matrix)
    cpu_corr = correlation_matrix.loc['process_time_ms', 'cpu_usage_percent']
    print(f"\n* Insight: The correlation between response time and CPU usage is {cpu_corr:.2f}. ")
    print("  (A value close to 1.0 means high CPU usage strongly relates to high response time. A value near 0 means little to no relation.)\n")

    # --- Insight 4: Top Failing Endpoints ---
    print("--- 4. Top Failing Endpoints ---")
    error_df = df[df['status_code'] >= 400]
    if not error_df.empty:
        failing_endpoints = error_df.groupby(['service', 'path']).size().sort_values(ascending=False)
        print(failing_endpoints.head(5)) # Show top 5
    else:
        print("No errors found in the logs!")
    print("\n* Insight: This shows exactly which specific endpoints are the source of most errors.\n")

# --- Main Execution Block ---
if __name__ == "__main__":
    df = load_all_logs_into_dataframe()
    run_analysis(df)