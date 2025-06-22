# import os
# import json
# import time
# from datetime import datetime, timedelta
# import google.generativeai as genai
# from dotenv import load_dotenv
# import logging
# from datetime import datetime, timedelta, timezone 

# # --- Basic Setup ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Load environment variables from .env file (for the API key)
# load_dotenv()

# # --- Configuration ---
# LOG_DIRECTORY = "logs"
# SERVICE_NAMES = ["auth-service", "order-service", "product-service"]
# ANALYSIS_INTERVAL_SECONDS = 65  # How often to run the analysis
# TIME_WINDOW_MINUTES = 5         # How far back to look in the logs
# ERROR_RATE_THRESHOLD = 0.10     # Trigger analysis if error rate is > 0%
# RESPONSE_TIME_THRESHOLD_MS = 400 # Trigger analysis if avg response time is > 400ms
# SUMMARY_FILE = "ai_summary.txt"

# # --- Configure the Gemini API ---
# # --- Configure the Gemini API ---
# try:
#     genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#     # Use the latest, most capable model name
#     model = genai.GenerativeModel('gemini-1.5-pro-latest') # <--- THE FIX
#     logging.info("Google Gemini configured successfully.")
# except Exception as e:
#     logging.error(f"Failed to configure Gemini API. Please check your API key. Error: {e}")
#     exit()

# # --- Core Functions ---
# def read_and_parse_logs():
#     """Reads logs from all service files within the time window."""
#     all_logs = []
#     end_time = datetime.now(timezone.utc)
#     start_time = end_time - timedelta(minutes=TIME_WINDOW_MINUTES)
    
#     for service_name in SERVICE_NAMES:
#         log_file_path = os.path.join(LOG_DIRECTORY, f"{service_name}.log")
#         if not os.path.exists(log_file_path):
#             continue
            
#         with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
#             for line in f:
#                 try:
#                     log_entry = json.loads(line)
                    
#                     # THE FIX IS HERE: We now use the 'repr' key, which exists in your log file.
#                     log_time_str = log_entry["record"]["time"]["repr"] 
                    
#                     log_time = datetime.fromisoformat(log_time_str)
                    
#                     # We must make the log_time UTC to compare with our start/end time
#                     log_time_utc = log_time.astimezone(timezone.utc)
                    
#                     if start_time <= log_time_utc <= end_time:
#                         all_logs.append(log_entry)
#                 except Exception as e:
#                     # You can leave this debug line in for now, or comment it out once it's working.
#                     # logging.error(f"Skipping line due to error: {e}")
#                     continue
#     return all_logs
# def aggregate_metrics(logs):
#     """Calculates key metrics per service from a list of logs."""
#     metrics = {service: {
#         "total_requests": 0, "errors": 0, "total_response_time_ms": 0,
#         "total_cpu": 0, "total_memory": 0, "error_messages": []
#     } for service in SERVICE_NAMES}

#     for log in logs:
#         try:
#             details = log["record"]["extra"]["json"]
#             service = details["service"]
            
#             if service in metrics:
#                 s_metrics = metrics[service]
#                 s_metrics["total_requests"] += 1
#                 s_metrics["total_response_time_ms"] += details["process_time_ms"]
#                 s_metrics["total_cpu"] += details["cpu_usage_percent"]
#                 s_metrics["total_memory"] += details["memory_usage_percent"]
                
#                 # Check for errors (status code >= 400 is considered an error)
#                 if details["status_code"] >= 400:
#                     s_metrics["errors"] += 1
#                     # Always capture the error message if available
#                     if "text" in log:
#                         s_metrics["error_messages"].append(log["text"])

#         except KeyError:
#             continue
            
#     # Calculate averages and rates
#     final_metrics = {}
#     for service, data in metrics.items():
#         total_reqs = data["total_requests"]
#         if total_reqs > 0:
#             final_metrics[service] = {
#                 "error_rate": data["errors"] / total_reqs,
#                 "avg_response_time_ms": data["total_response_time_ms"] / total_reqs,
#                 "avg_cpu_percent": data["total_cpu"] / total_reqs,
#                 "avg_memory_percent": data["total_memory"] / total_reqs,
#                 "error_count": data["errors"],
#                 "total_requests": total_reqs,
#                 "distinct_errors": list(set(data["error_messages"]))[:3] # Get up to 3 unique errors
#             }
#     return final_metrics

# def check_for_anomalies(metrics):
#     """Checks if any metric has crossed its defined threshold."""
#     anomalies = {}
#     for service, data in metrics.items():
#         is_anomaly = False
#         if data["error_rate"] > ERROR_RATE_THRESHOLD:
#             is_anomaly = True
#         if data["avg_response_time_ms"] > RESPONSE_TIME_THRESHOLD_MS:
#             is_anomaly = True
        
#         if is_anomaly:
#             anomalies[service] = data
#     return anomalies

# def generate_ai_summary(anomalous_metrics):
#     """Formats a prompt and calls the Gemini API for analysis."""
#     if not anomalous_metrics:
#         return "No anomalies detected."

#     # This is the prompt engineering part. We give the AI a role, context, data, and a desired format.
#     prompt = f"""
#     You are an expert Site Reliability Engineer (SRE). Your task is to analyze the following system health metrics and provide a root cause analysis summary.

#     **Analysis Time Window:** Last {TIME_WINDOW_MINUTES} minutes.

#     **Anomalous Metrics Detected:**
#     ```json
#     {json.dumps(anomalous_metrics, indent=2)}
#     ```

#     **Instructions:**
#     Based on the data above, please provide a concise, human-readable summary covering these three points:
#     1.  **Overall Health Status:** A one-sentence summary of the system's current state (e.g., "System is degraded," "Critical error in payment service").
#     2.  **Likely Root Cause:** Based on the metrics (especially error messages, high response times, or high error rates), what is the most likely problem? For example, is a specific service failing? Is there a database connection issue? Be specific.
#     3.  **Recommended Action:** What is the immediate next step a developer should take to investigate? (e.g., "Check the logs for 'order-service' for database connection errors," "Investigate the high latency in 'product-service'").
#     """
    
#     try:
#         logging.info("Sending request to Gemini API for analysis...")
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         logging.error(f"Error calling Gemini API: {e}")
#         return f"Error: Could not get analysis from AI. Details: {e}"

# # --- Main Loop ---
# if __name__ == "__main__":
#     while True:
#         logging.info("--- Running new analysis cycle ---")
        
#         # 1. Read and parse logs
#         logs = read_and_parse_logs()
#         logging.info(f"Parsed logs: {json.dumps(logs, indent=2)}")
#         if not logs:
#             logging.info("No new logs found in the time window. Waiting...")
#             time.sleep(ANALYSIS_INTERVAL_SECONDS)
#             continue
            
#         # 2. Aggregate metrics
#         metrics = aggregate_metrics(logs)
#         logging.info(f"Aggregated Metrics: {json.dumps(metrics, indent=2)}")
        
#         # 3. Check for problems
#         anomalies = check_for_anomalies(metrics)
        
#         # 4. If problems exist, get AI summary
#         if anomalies:
#             logging.warning(f"Anomaly detected in services: {list(anomalies.keys())}")
#             ai_summary = generate_ai_summary(anomalies)
#             logging.info(f"\n--- AI ANALYSIS ---\n{ai_summary}\n-------------------\n")
            
#             # 5. Save the summary to a file for the frontend to read
#             with open(SUMMARY_FILE, 'w') as f:
#                 f.write(ai_summary)
#         else:
#             logging.info("All systems operating within normal parameters.")
#             # Clear the summary file if everything is okay
#             with open(SUMMARY_FILE, 'w') as f:
#                 f.write("All systems are healthy.")

#         time.sleep(ANALYSIS_INTERVAL_SECONDS)
import os
import json
import time
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import pandas as pd
import warnings
import asyncio

# --- New Imports for the API Server ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Ignore pandas warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# --- Configuration ---
LOG_DIRECTORY = "logs"
SERVICE_NAMES = ["auth-service", "order-service", "product-service"]
SUMMARY_FILE = "ai_summary.txt"
TIME_WINDOW_MINUTES = 5
ANALYSIS_INTERVAL_SECONDS = 65  # Keep this above 60 to be safe
ERROR_RATE_THRESHOLD = 0.10
RESPONSE_TIME_THRESHOLD_MS = 500

# --- State Management (in-memory) ---
latest_metrics = {}
latest_summary = "Starting up..."

# --- 1. MODIFIED: CONFIGURE GEMINI API ON STARTUP ---
# We now initialize the model here, ONCE, and store it in a global variable.
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file. Please check your .env file.")
    
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
    logging.info("Google Gemini configured successfully.")
except Exception as e:
    logging.error(f"Failed to configure Gemini API on startup. AI features will be disabled. Error: {e}")
    gemini_model = None  # Set to None if initialization fails

# --- FastAPI App Initialization ---
app = FastAPI()

# --- CORS Middleware Setup ---
origins = ["http://localhost:3000", "http://localhost"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Processing Functions ---
# (These functions are unchanged and correct)

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
    agg_df = df.groupby('service').agg(
        total_requests=('service', 'count'),
        avg_response_time_ms=('process_time_ms', 'mean'),
        avg_cpu_percent=('cpu_usage_percent', 'mean')
    ).reset_index()
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
        is_anomaly = (data.get("error_rate", 0) > ERROR_RATE_THRESHOLD) or \
                     (data.get("avg_response_time_ms", 0) > RESPONSE_TIME_THRESHOLD_MS)
        if is_anomaly:
            anomalies[service] = data
    return anomalies

def perform_traditional_analysis(df):
    if df.empty: return {"error": "Not enough data to perform analysis."}
    insights = {}
    performance_summary = df.groupby('service').agg(total_requests=('service', 'count'), avg_response_time_ms=('process_time_ms', 'mean'), avg_cpu_percent=('cpu_usage_percent', 'mean'), error_rate=('status_code', lambda x: (x >= 400).mean() * 100)).round(2)
    insights['performance_summary'] = performance_summary.reset_index().to_dict(orient='records')
    df_time_indexed = df.set_index(pd.to_datetime(df['timestamp']))
    requests_per_minute = df_time_indexed.resample('1min').size()
    if not requests_per_minute.empty:
        busiest_minute = requests_per_minute.idxmax()
        request_count = requests_per_minute.max()
        insights['busiest_period'] = {"minute": busiest_minute.strftime('%Y-%m-%d %H:%M:%S UTC'), "request_count": int(request_count)}
    correlation_matrix = df[['process_time_ms', 'cpu_usage_percent', 'memory_usage_percent']].corr()
    insights['correlation_matrix'] = correlation_matrix.to_dict()
    error_df = df[df['status_code'] >= 400]
    if not error_df.empty:
        failing_endpoints = error_df.groupby(['service', 'path']).size().sort_values(ascending=False).head(5)
        insights['failing_endpoints'] = failing_endpoints.reset_index(name='count').to_dict(orient='records')
    else:
        insights['failing_endpoints'] = []
    return insights

# --- 2. MODIFIED: AI SUMMARY FUNCTION ---
# It now accepts the model object as an argument and does NOT configure the API inside.
def generate_ai_summary(model, anomalous_metrics):
    """Formats a prompt and calls the Gemini API for analysis."""
    if not model:
        return "Error: Gemini model was not initialized correctly on startup. AI analysis is disabled."
    if not anomalous_metrics:
        return "All systems are operating within normal parameters."

    prompt = f"""
    You are an SRE. Analyze these metrics and provide a root cause summary.
    Analysis Time Window: Last {TIME_WINDOW_MINUTES} minutes.
    Anomalous Metrics:
    ```json
    {json.dumps(anomalous_metrics, indent=2)}
    ```
    Instructions: Provide a concise, 3-point summary: Overall Health, Likely Root Cause, Recommended Action.
    """
    try:
        # The only AI-related line needed here.
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return f"Error: Could not get analysis from AI. Details: {e}"

# --- Background Monitoring Task ---
async def monitoring_loop():
    global latest_metrics, latest_summary
    while True:
        logging.info("--- Running new analysis cycle ---")
        log_df = read_and_parse_logs()
        metrics = aggregate_metrics(log_df)
        latest_metrics = metrics
        
        anomalies = check_for_anomalies(metrics)
        if anomalies:
            logging.warning(f"Anomaly detected in services: {list(anomalies.keys())}")
            # --- 3. MODIFIED: PASS THE MODEL OBJECT ---
            # We now pass the globally-initialized 'gemini_model' to the function.
            ai_summary = generate_ai_summary(gemini_model, anomalies)
            latest_summary = ai_summary
        else:
            latest_summary = "All systems are operating within normal parameters."
        
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write(latest_summary)
            
        await asyncio.sleep(ANALYSIS_INTERVAL_SECONDS)

# --- API Endpoints ---
# (These endpoints are unchanged and correct)

@app.get("/api/metrics")
async def get_metrics():
    return latest_metrics

@app.get("/api/summary")
async def get_summary():
    return {"summary": latest_summary}

@app.get("/api/traditional-analysis")
async def get_traditional_analysis():
    all_log_data = []
    for service_name in SERVICE_NAMES:
        log_file_path = os.path.join(LOG_DIRECTORY, f"{service_name}.log")
        if not os.path.exists(log_file_path): continue
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    flat_log = log_entry["record"]["extra"]["json"]
                    flat_log['timestamp'] = log_entry["record"]["time"]["repr"]
                    all_log_data.append(flat_log)
                except: continue
    
    if not all_log_data: return {"error": "No log data available to analyze."}
    df = pd.DataFrame(all_log_data)
    analysis_results = perform_traditional_analysis(df)
    return analysis_results

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitoring_loop())

# --- Main execution block ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)