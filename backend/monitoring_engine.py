import os
import json
import time
from datetime import datetime, timedelta, timezone
import ollama
import logging
import pandas as pd
import warnings
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# --- Setup (Unchanged) ---
warnings.simplefilter(action='ignore', category=FutureWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOG_DIRECTORY = "logs"
SERVICE_NAMES = ["auth-service", "order-service", "product-service"]
SUMMARY_FILE = "ai_summary.txt"
TIME_WINDOW_MINUTES = 5
ANALYSIS_INTERVAL_SECONDS = 20
ERROR_RATE_THRESHOLD = 0.10
RESPONSE_TIME_THRESHOLD_MS = 500
latest_metrics = {}
latest_summary = "Starting up..."

# Configure Ollama client
ollama_client = ollama.Client(host='http://host.docker.internal:11434')

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Data Processing Functions (Unchanged) ---
def read_and_parse_logs():
    all_log_data = []
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=TIME_WINDOW_MINUTES)
    for service_name in SERVICE_NAMES:
        log_file_path = os.path.join(LOG_DIRECTORY, f"{service_name}.log")
        if not os.path.exists(log_file_path): continue
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    log_time = datetime.fromisoformat(log_entry["record"]["time"]["repr"]).astimezone(timezone.utc)
                    if start_time <= log_time <= end_time:
                        all_log_data.append(log_entry["record"]["extra"]["json"])
                except: continue
    if not all_log_data: return pd.DataFrame()
    return pd.DataFrame(all_log_data)

def aggregate_metrics(df):
    if df.empty: return {}
    agg_df = df.groupby('service').agg(total_requests=('service', 'count'),avg_response_time_ms=('process_time_ms', 'mean'),avg_cpu_percent=('cpu_usage_percent', 'mean')).reset_index()
    error_df = df[df['status_code'] >= 400].groupby('service').agg(error_count=('service', 'count')).reset_index()
    if not error_df.empty:
        agg_df = pd.merge(agg_df, error_df, on='service', how='left').fillna(0)
    else:
        agg_df['error_count'] = 0
    agg_df['error_rate'] = (agg_df['error_count'] / agg_df['total_requests']) * 100
    return {row['service']: row.to_dict() for _, row in agg_df.iterrows()}

def check_for_anomalies(metrics):
    anomalies = {}
    for service, data in metrics.items():
        if (data.get("error_rate", 0) > ERROR_RATE_THRESHOLD) or (data.get("avg_response_time_ms", 0) > RESPONSE_TIME_THRESHOLD_MS):
            anomalies[service] = data
    return anomalies

def generate_ai_summary(anomalous_metrics):
    if not anomalous_metrics:
        return "All systems are operating within normal parameters."
    
    prompt = f"""You are a Site Reliability Engineer (SRE) analyzing system anomalies. Based on the following metrics data, provide a concise analysis of the issues and recommended actions:

{json.dumps(anomalous_metrics, indent=2)}

Please provide:
1. A brief summary of the anomalies detected
2. Potential root causes
3. Recommended immediate actions
4. Any patterns or correlations you notice

Keep your response focused and actionable."""
    
    try:
        response = ollama_client.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        return f"Error: Could not get analysis from AI. Details: {e}"


# --- `perform_traditional_analysis` (Simplified again) ---
# It now expects a DataFrame that already has a proper DatetimeIndex
def perform_traditional_analysis(df_with_datetime_index):
    df = df_with_datetime_index
    if df.empty:
        return {"error": "Not enough data to perform analysis."}

    insights = {}
    
    # Performance Summary
    performance_summary = df.groupby('service').agg(total_requests=('service', 'count'), avg_response_time_ms=('process_time_ms', 'mean'), avg_cpu_percent=('cpu_usage_percent', 'mean'), error_rate=('status_code', lambda x: (x >= 400).mean() * 100)).round(2)
    insights['performance_summary'] = performance_summary.reset_index().to_dict(orient='records')
    
    # Busiest Period - This will now work
    requests_per_minute = df.resample('1min').size()
    if not requests_per_minute.empty:
        busiest_minute = requests_per_minute.idxmax()
        insights['busiest_period'] = {"minute": busiest_minute.strftime('%Y-%m-%d %H:%M:%S UTC'), "request_count": int(requests_per_minute.max())}
    
    # Correlation
    corr_cols = ['process_time_ms', 'cpu_usage_percent', 'memory_usage_percent']
    if all(col in df.columns for col in corr_cols):
        insights['correlation_matrix'] = df[corr_cols].corr().to_dict()
    
    # Top Failing Endpoints
    error_df = df[df['status_code'] >= 400]
    if not error_df.empty:
        failing_endpoints = error_df.groupby(['service', 'path']).size().sort_values(ascending=False).head(5)
        insights['failing_endpoints'] = failing_endpoints.reset_index(name='count').to_dict(orient='records')
    else:
        insights['failing_endpoints'] = []
        
    return insights

# --- Analysis Loop (Unchanged) ---
async def run_analysis_cycle():
    global latest_metrics, latest_summary
    log_df = read_and_parse_logs()
    metrics = aggregate_metrics(log_df)
    latest_metrics = metrics
    anomalies = check_for_anomalies(metrics)
    if anomalies: latest_summary = generate_ai_summary(anomalies)
    else: latest_summary = "All systems are operating within normal parameters."
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f: f.write(latest_summary)

async def monitoring_loop():
    await run_analysis_cycle()
    while True:
        await asyncio.sleep(ANALYSIS_INTERVAL_SECONDS)
        await run_analysis_cycle()

# --- API Endpoints ---
@app.get("/api/metrics")
async def get_metrics(): return latest_metrics
@app.get("/api/summary")
async def get_summary(): return {"summary": latest_summary}


# --- THE FINAL FIX IS HERE: `get_traditional_analysis` ---
@app.get("/api/traditional-analysis")
async def get_traditional_analysis():
    try:
        all_log_data = []
        for service_name in SERVICE_NAMES:
            log_file_path = os.path.join(LOG_DIRECTORY, f"{service_name}.log")
            if not os.path.exists(log_file_path): continue
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        flat_log = log_entry["record"]["extra"]["json"]
                        
                        # --- IMPROVED TIMESTAMP HANDLING ---
                        ts_repr = log_entry["record"]["time"]["repr"]
                        
                        # More robust timezone offset handling
                        # Handle formats like: 2025-06-23T13:17:30.123456+05:30
                        if '+' in ts_repr and ts_repr.count(':') > 2:
                            # Split at the last colon in the timezone part
                            base_part, tz_minutes = ts_repr.rsplit(':', 1)
                            if '+' in base_part:
                                dt_part, tz_hours = base_part.rsplit('+', 1)
                                ts_repr = f"{dt_part}+{tz_hours}{tz_minutes}"
                        elif '-' in ts_repr and ts_repr.count(':') > 2:
                            # Handle negative timezone offsets
                            parts = ts_repr.split('-')
                            if len(parts) >= 2 and ':' in parts[-1]:
                                tz_part = parts[-1]
                                if tz_part.count(':') == 1:
                                    tz_hours, tz_minutes = tz_part.split(':')
                                    ts_repr = ts_repr.replace(f"-{tz_part}", f"-{tz_hours}{tz_minutes}")
                        # --- END IMPROVED FIX ---

                        flat_log['timestamp'] = ts_repr
                        all_log_data.append(flat_log)
                    except Exception as parse_error:
                        logging.debug(f"Failed to parse log line: {parse_error}")
                        continue
        
        if not all_log_data:
            return {"error": "No log data available to analyze."}
            
        df = pd.DataFrame(all_log_data)
        logging.info(f"Created DataFrame with {len(df)} rows")
        
        # Debug: Print some sample timestamps before conversion
        if len(df) > 0:
            logging.info(f"Sample timestamps: {df['timestamp'].head().tolist()}")
        
        # More flexible timestamp conversion
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        
        # Log how many timestamps failed to convert
        null_timestamps = df['timestamp'].isnull().sum()
        if null_timestamps > 0:
            logging.warning(f"{null_timestamps} timestamps failed to convert")
        
        df.dropna(subset=['timestamp'], inplace=True)
        logging.info(f"After timestamp conversion: {len(df)} rows remaining")
        
        if df.empty:
            return {"error": "No valid timestamps found in log data."}
        
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            logging.error("Timestamp column is not datetime type")
            return {"error": "Failed to convert timestamps to datetime objects."}
            
        df.set_index('timestamp', inplace=True)
        
        # Ensure timezone consistency
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')

        analysis_results = perform_traditional_analysis(df)
        return analysis_results
        
    except Exception as e:
        logging.error("--- TRADITIONAL ANALYSIS: FAILED ---", exc_info=True)
        return {"error": f"Analysis failed: {str(e)}"}

# --- Historical Metrics Endpoint ---
@app.get("/api/metrics/historical")
async def get_historical_metrics():
    try:
        all_log_data = []
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=15)
        for service_name in SERVICE_NAMES:
            log_file_path = os.path.join(LOG_DIRECTORY, f"{service_name}.log")
            if not os.path.exists(log_file_path):
                continue
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        flat_log = log_entry["record"]["extra"]["json"]
                        ts_repr = log_entry["record"]["time"]["repr"]
                        # --- IMPROVED TIMESTAMP HANDLING (copied from /api/traditional-analysis) ---
                        if '+' in ts_repr and ts_repr.count(':') > 2:
                            base_part, tz_minutes = ts_repr.rsplit(':', 1)
                            if '+' in base_part:
                                dt_part, tz_hours = base_part.rsplit('+', 1)
                                ts_repr = f"{dt_part}+{tz_hours}{tz_minutes}"
                        elif '-' in ts_repr and ts_repr.count(':') > 2:
                            parts = ts_repr.split('-')
                            if len(parts) >= 2 and ':' in parts[-1]:
                                tz_part = parts[-1]
                                if tz_part.count(':') == 1:
                                    tz_hours, tz_minutes = tz_part.split(':')
                                    ts_repr = ts_repr.replace(f"-{tz_part}", f"-{tz_hours}{tz_minutes}")
                        flat_log['timestamp'] = ts_repr
                        all_log_data.append(flat_log)
                    except Exception as parse_error:
                        logging.debug(f"Failed to parse log line: {parse_error}")
                        continue
        if not all_log_data:
            return []
        df = pd.DataFrame(all_log_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        df.dropna(subset=['timestamp'], inplace=True)
        df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
        if df.empty:
            return []
        df.set_index('timestamp', inplace=True)
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
        # Prepare output: for each service, resample by 1min, calculate mean latency and error count
        result_frames = []
        for service in SERVICE_NAMES:
            service_df = df[df['service'] == service]
            if service_df.empty:
                continue
            resampled = service_df.resample('1min').agg({
                'process_time_ms': 'mean',
                'status_code': lambda x: (x >= 400).sum()
            }).rename(columns={
                'process_time_ms': f'{service}_latency',
                'status_code': f'{service}_error_count'
            })
            result_frames.append(resampled[[f'{service}_latency', f'{service}_error_count']])
        if not result_frames:
            return []
        merged = pd.concat(result_frames, axis=1)
        merged = merged.sort_index()
        # Format output as list of dicts
        output = []
        for idx, row in merged.iterrows():
            entry = {'time': idx.strftime('%Y-%m-%dT%H:%M:%SZ')}
            for col in merged.columns:
                val = row[col]
                if pd.isna(val):
                    val = 0
                if col.endswith('_latency'):
                    entry[col] = round(float(val), 2)
                else:
                    entry[col] = int(val)
            output.append(entry)
        return output
    except Exception as e:
        logging.error("--- HISTORICAL METRICS: FAILED ---", exc_info=True)
        return []

# --- Startup ---
@app.on_event("startup")
async def startup_event(): asyncio.create_task(monitoring_loop())
if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8008)