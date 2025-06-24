import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css"; // We'll add some basic styles
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// The base URL for our Python backend API
const API_BASE_URL = "http://localhost:8008";

function App() {
  // State variables to hold our data
  const [metrics, setMetrics] = useState({});
  const [summary, setSummary] = useState("Loading analysis...");
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [chartData, setChartData] = useState([]);

  // This function fetches data from our backend
  const fetchData = async () => {
    try {
      const metricsResponse = await axios.get(`${API_BASE_URL}/api/metrics`);
      setMetrics(metricsResponse.data);

      const summaryResponse = await axios.get(`${API_BASE_URL}/api/summary`);
      setSummary(summaryResponse.data.summary);
    } catch (error) {
      console.error("Error fetching data:", error);
      setSummary("Could not connect to the backend monitoring engine.");
    }
  };
  const fetchTraditionalAnalysis = async () => {
    setIsLoadingAnalysis(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/traditional-analysis`
      );
      setAnalysisData(response.data);
    } catch (error) {
      console.error("Error fetching traditional analysis:", error);
      setAnalysisData({ error: "Failed to load analysis data." });
    }
    setIsLoadingAnalysis(false);
  };
  // useEffect hook to fetch data on component mount and then poll every 15 seconds
  useEffect(() => {
    fetchData(); // Fetch immediately on load
    const fetchChartData = async () => {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/metrics/historical`
        );
        setChartData(response.data);
      } catch (error) {
        setChartData([]);
      }
    };
    fetchChartData();
    const interval = setInterval(() => {
      fetchData();
      fetchChartData();
    }, 15000); // 15000 ms = 15 seconds
    return () => clearInterval(interval);
  }, []);

  // Get the service names from the metrics data keys
  const serviceNames = Object.keys(metrics);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AI-Powered Microservice Health Dashboard</h1>
        <p>
          Displaying real-time data. Last updated:{" "}
          {new Date().toLocaleTimeString()}
        </p>
      </header>

      <main>
        <div className="summary-card">
          <h2>💡 GenAI Root Cause Analysis</h2>
          <pre>{summary}</pre>
        </div>

        <MetricsLineChart chartData={chartData} />

        <div className="traditional-analysis-section">
          <button
            onClick={fetchTraditionalAnalysis}
            disabled={isLoadingAnalysis}
          >
            {isLoadingAnalysis
              ? "Analyzing..."
              : "Run Traditional Data Analysis"}
          </button>

          {analysisData && (
            <div className="analysis-results">
              <h3>Historical Data Insights</h3>
              {analysisData.error ? (
                <p className="error-message">{analysisData.error}</p>
              ) : (
                // We will create a component to display this data nicely
                <AnalysisResults data={analysisData} />
              )}
            </div>
          )}
        </div>
        <div className="metrics-grid">
          {serviceNames.length > 0 ? (
            serviceNames.map((serviceName) => (
              <ServiceCard
                key={serviceName}
                serviceName={serviceName}
                data={metrics[serviceName]}
              />
            ))
          ) : (
            <p>Waiting for metrics data...</p>
          )}
        </div>
      </main>
    </div>
  );
}

// A reusable component for displaying each service's metrics
// A reusable component for displaying each service's metrics
const ServiceCard = ({ serviceName, data }) => {
  const errorRate = data.error_rate || 0;
  let healthStatus = "healthy";
  if (errorRate > 10) healthStatus = "unhealthy";
  else if (errorRate > 0) healthStatus = "degraded";

  // THE FIX IS HERE: Create our own title-casing logic.
  const formattedServiceName = serviceName
    .replace("-", " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  return (
    <div className={`service-card ${healthStatus}`}>
      {/* Use the new formatted variable here */}
      <h3>{formattedServiceName}</h3>
      <div className="metric">
        {/* ... rest of the component is the same ... */}
        <span className="metric-label">Error Rate</span>
        <span className="metric-value">{errorRate.toFixed(2)} %</span>
      </div>
      <div className="metric">
        <span className="metric-label">Avg. Response Time</span>
        <span className="metric-value">
          {data.avg_response_time_ms.toFixed(2)} ms
        </span>
      </div>
      <div className="metric">
        <span className="metric-label">Avg. CPU Usage</span>
        <span className="metric-value">
          {data.avg_cpu_percent.toFixed(2)} %
        </span>
      </div>
      <div className="metric">
        <span className="metric-label">Total Requests</span>
        <span className="metric-value">{data.total_requests}</span>
      </div>
    </div>
  );
};
// Place this new component at the bottom of App.js, before 'export default App;'

const AnalysisResults = ({ data }) => {
  return (
    <div className="grid-container">
      <div className="grid-item">
        <h4>Overall Performance</h4>
        <table>
          <thead>
            <tr>
              <th>Service</th>
              <th>Total Requests</th>
              <th>Avg. Response (ms)</th>
              <th>Error Rate (%)</th>
            </tr>
          </thead>
          <tbody>
            {data.performance_summary?.map((item) => (
              <tr key={item.service}>
                <td>{item.service}</td>
                <td>{item.total_requests}</td>
                <td>{item.avg_response_time_ms}</td>
                <td>{item.error_rate.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid-item">
        <h4>Top Failing Endpoints</h4>
        {data.failing_endpoints?.length > 0 ? (
          <ul>
            {data.failing_endpoints.map((item) => (
              <li key={`${item.service}-${item.path}`}>
                <strong>{item.path}</strong> ({item.service}): {item.count}{" "}
                errors
              </li>
            ))}
          </ul>
        ) : (
          <p>No failing endpoints found.</p>
        )}
      </div>

      <div className="grid-item">
        <h4>Busiest Period</h4>
        {data.busiest_period ? (
          <p>
            <strong>{data.busiest_period.minute}</strong> with{" "}
            <strong>{data.busiest_period.request_count}</strong> requests.
          </p>
        ) : (
          <p>Not enough data.</p>
        )}
      </div>
    </div>
  );
};

const MetricsLineChart = ({ chartData }) => {
  // Dynamically get all keys ending with '_latency'
  const latencyKeys =
    chartData.length > 0
      ? Object.keys(chartData[0]).filter((key) => key.endsWith("_latency"))
      : [];

  const colors = [
    "#8884d8",
    "#82ca9d",
    "#ff7300",
    "#ff0000",
    "#0088FE",
    "#00C49F",
  ];

  return (
    <div className="chart-card">
      <h2>📈 Service Latency (Last 15 Minutes)</h2>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            minTickGap={30}
            tickFormatter={(t) => t.slice(11, 16)}
          />
          <YAxis label={{ value: "ms", angle: -90, position: "insideLeft" }} />
          <Tooltip />
          <Legend />
          {latencyKeys.map((key, idx) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[idx % colors.length]}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default App;
