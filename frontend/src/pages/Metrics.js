import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { apiService, dataUtils } from "../services/api";
import {
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import MetricCard from "../components/MetricCard";
import toast from "react-hot-toast";

const Metrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [prometheusData, setPrometheusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Chart colors
  const colors = {
    primary: "#3b82f6",
    success: "#22c55e",
    warning: "#f59e0b",
    danger: "#ef4444",
    gray: "#6b7280",
  };

  // Fetch metrics data
  const fetchMetricsData = async () => {
    try {
      setLoading(true);
      const [metricsData, prometheusStatus] = await Promise.all([
        apiService.getMetrics(),
        apiService.getPrometheusStatus(),
      ]);

      setMetrics(metricsData);
      setPrometheusData(prometheusStatus);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
      toast.error("Failed to load metrics data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsData();
    const interval = setInterval(fetchMetricsData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Generate mock time series data for charts
  const generateTimeSeriesData = (baseValue, variance = 0.2, points = 24) => {
    const data = [];
    const now = new Date();

    for (let i = points - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 15 * 60 * 1000); // 15-minute intervals
      const value = baseValue + (Math.random() - 0.5) * variance * baseValue;
      data.push({
        time: time.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        value: Math.max(0, Math.round(value)),
      });
    }
    return data;
  };

  // Prepare chart data
  const chartData = {
    httpRequests: generateTimeSeriesData(150, 0.3),
    responseTime: generateTimeSeriesData(200, 0.4).map((d) => ({
      ...d,
      value: d.value / 1000,
    })),
    errorRate: generateTimeSeriesData(5, 0.5),
    cpuUsage: generateTimeSeriesData(45, 0.2),
    memoryUsage: generateTimeSeriesData(60, 0.15),
  };

  // Response code distribution
  const responseCodes = [
    { name: "2xx Success", value: 85, color: colors.success },
    { name: "4xx Client Error", value: 10, color: colors.warning },
    { name: "5xx Server Error", value: 5, color: colors.danger },
  ];

  // Service metrics
  const serviceMetrics = [
    {
      title: "HTTP Requests",
      value: metrics?.log_metrics?.total || 0,
      subtitle: "Total requests",
      icon: ChartBarIcon,
      color: "primary",
    },
    {
      title: "Error Rate",
      value: `${metrics?.log_metrics?.performance_metrics?.error_rate || 0}%`,
      subtitle: "Last hour",
      icon: ExclamationTriangleIcon,
      color: "danger",
    },
    {
      title: "Avg Response Time",
      value: dataUtils.formatDuration(
        metrics?.log_metrics?.performance_metrics?.avg_latency_ms / 1000
      ),
      subtitle: "Request latency",
      icon: ClockIcon,
      color: "warning",
    },
    {
      title: "Active Services",
      value:
        prometheusData?.targets?.filter((t) => t.health === "up").length || 0,
      subtitle: "Healthy targets",
      icon: ChartBarIcon,
      color: "success",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Metrics & Analytics
          </h1>
          <p className="text-gray-600">
            Prometheus metrics and performance data
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          <button
            onClick={fetchMetricsData}
            disabled={loading}
            className="btn btn-primary"
          >
            <ArrowPathIcon
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {serviceMetrics.map((metric, index) => (
          <MetricCard
            key={index}
            title={metric.title}
            value={metric.value}
            subtitle={metric.subtitle}
            icon={metric.icon}
            color={metric.color}
            loading={loading}
          />
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* HTTP Requests Over Time */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">HTTP Requests Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData.httpRequests}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="value"
                stroke={colors.primary}
                fill={colors.primary}
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Response Time Over Time */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Response Time Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData.responseTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}s`, "Response Time"]} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={colors.warning}
                strokeWidth={2}
                dot={{ fill: colors.warning, strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Error Rate Over Time */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Error Rate Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData.errorRate}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, "Error Rate"]} />
              <Bar dataKey="value" fill={colors.danger} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Response Code Distribution */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Response Code Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={responseCodes}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {responseCodes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU Usage */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">CPU Usage Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData.cpuUsage}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, "CPU Usage"]} />
              <Area
                type="monotone"
                dataKey="value"
                stroke={colors.success}
                fill={colors.success}
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Memory Usage */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Memory Usage Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData.memoryUsage}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, "Memory Usage"]} />
              <Area
                type="monotone"
                dataKey="value"
                stroke={colors.primary}
                fill={colors.primary}
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Prometheus Status */}
      {prometheusData && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Prometheus Metrics Summary</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {prometheusData.metrics_summary?.http_requests || 0}
              </div>
              <div className="text-sm text-gray-500">HTTP Requests</div>
            </div>

            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {prometheusData.metrics_summary?.auth_attempts || 0}
              </div>
              <div className="text-sm text-gray-500">Auth Attempts</div>
            </div>

            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {prometheusData.metrics_summary?.jwt_tokens || 0}
              </div>
              <div className="text-sm text-gray-500">JWT Tokens</div>
            </div>

            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {prometheusData.metrics_summary?.errors || 0}
              </div>
              <div className="text-sm text-gray-500">Total Errors</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Metrics;
