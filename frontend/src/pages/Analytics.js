import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
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
  LightBulbIcon,
  CpuChipIcon,
  ServerIcon,
} from "@heroicons/react/24/outline";
import MetricCard from "../components/MetricCard";
import StatusBadge from "../components/StatusBadge";
import toast from "react-hot-toast";

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [rootCause, setRootCause] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Chart colors
  const colors = {
    primary: "#3b82f6",
    success: "#22c55e",
    warning: "#f59e0b",
    danger: "#ef4444",
    gray: "#6b7280",
    purple: "#8b5cf6",
  };

  // Fetch analytics data
  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const [analyticsData, performanceData] = await Promise.all([
        apiService.getAnalytics(),
        apiService.getPerformance(),
      ]);

      setAnalytics(analyticsData);
      setPerformance(performanceData);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      toast.error("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  };

  // Fetch AI root cause analysis
  const fetchRootCauseAnalysis = async () => {
    try {
      setAiLoading(true);
      const analysis = await apiService.getRootCause();
      setRootCause(analysis);
      toast.success("AI analysis completed");
    } catch (error) {
      console.error("Failed to fetch root cause analysis:", error);
      toast.error("Failed to get AI analysis");
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
    const interval = setInterval(fetchAnalyticsData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Generate mock time series data for charts
  const generateTimeSeriesData = (baseValue, variance = 0.2, points = 12) => {
    const data = [];
    const now = new Date();

    for (let i = points - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 30 * 60 * 1000); // 30-minute intervals
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
    errorRate: generateTimeSeriesData(8, 0.4),
    latency: generateTimeSeriesData(250, 0.3).map((d) => ({
      ...d,
      value: d.value / 1000,
    })),
    throughput: generateTimeSeriesData(120, 0.25),
    cpuUsage: generateTimeSeriesData(50, 0.2),
  };

  // Error type distribution
  const errorTypes = analytics?.log_analytics?.error_types || {};
  const errorTypeData = Object.entries(errorTypes).map(
    ([type, count], index) => ({
      name: type.replace(/_/g, " ").toUpperCase(),
      value: count,
      color: [colors.danger, colors.warning, colors.gray, colors.purple][
        index % 4
      ],
    })
  );

  // Service performance data
  const servicePerformance = performance?.service_performance || {};
  const serviceData = Object.entries(servicePerformance).map(
    ([service, data]) => ({
      service,
      avgLatency: data.avg_latency || 0,
      totalRequests: data.total_requests || 0,
      errors: data.errors || 0,
    })
  );

  // Key metrics
  const keyMetrics = [
    {
      title: "Total Requests",
      value: analytics?.log_analytics?.total_requests || 0,
      subtitle: "Last hour",
      icon: ChartBarIcon,
      color: "primary",
    },
    {
      title: "Error Rate",
      value: analytics?.log_analytics?.error_rate || "0%",
      subtitle: "System health",
      icon: ExclamationTriangleIcon,
      color: "danger",
    },
    {
      title: "Avg Response Time",
      value: dataUtils.formatDuration(
        performance?.latency_analysis?.average_ms / 1000
      ),
      subtitle: "Performance",
      icon: ClockIcon,
      color: "warning",
    },
    {
      title: "Success Rate",
      value: performance?.throughput?.success_rate || "0%",
      subtitle: "Reliability",
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
            Analytics & AI Insights
          </h1>
          <p className="text-gray-600">
            Advanced analytics and AI-powered root cause analysis
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          <button
            onClick={fetchAnalyticsData}
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
        {keyMetrics.map((metric, index) => (
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

      {/* AI Root Cause Analysis */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CpuChipIcon className="w-5 h-5 text-purple-600" />
              <h2 className="card-title">AI Root Cause Analysis</h2>
            </div>
            <button
              onClick={fetchRootCauseAnalysis}
              disabled={aiLoading}
              className="btn btn-secondary"
            >
              <LightBulbIcon
                className={`w-4 h-4 mr-2 ${aiLoading ? "animate-spin" : ""}`}
              />
              {aiLoading ? "Analyzing..." : "Run Analysis"}
            </button>
          </div>
        </div>

        <div className="p-6">
          {rootCause ? (
            <div className="space-y-4">
              {rootCause.anomalies && rootCause.anomalies.length > 0 ? (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Detected Anomalies
                  </h3>
                  <div className="space-y-2">
                    {rootCause.anomalies.map((anomaly, index) => (
                      <div
                        key={index}
                        className="flex items-start space-x-3 p-3 bg-red-50 border border-red-200 rounded-lg"
                      >
                        <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                        <span className="text-red-800">{anomaly}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center space-x-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <ServerIcon className="w-5 h-5 text-green-500" />
                  <span className="text-green-800">
                    No anomalies detected - system is healthy
                  </span>
                </div>
              )}

              {rootCause.root_cause && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    AI Analysis
                  </h3>
                  <div className="prose prose-sm max-w-none">
                    <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                      <pre className="whitespace-pre-wrap text-gray-800 font-mono text-sm">
                        {rootCause.root_cause}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <LightBulbIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                Click "Run Analysis" to get AI-powered insights
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error Rate Over Time */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Error Rate Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData.errorRate}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, "Error Rate"]} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={colors.danger}
                strokeWidth={2}
                dot={{ fill: colors.danger, strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Latency Over Time */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Response Latency Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData.latency}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}s`, "Latency"]} />
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
      </div>

      {/* Error Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error Type Distribution */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Error Type Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={errorTypeData}
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
                {errorTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Service Performance */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Service Performance</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={serviceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service" />
              <YAxis />
              <Tooltip />
              <Bar
                dataKey="avgLatency"
                fill={colors.primary}
                name="Avg Latency (ms)"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Response Codes */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Response Code Distribution</h2>
          </div>
          <div className="p-6">
            {analytics?.log_analytics?.response_codes ? (
              <div className="space-y-3">
                {Object.entries(analytics.log_analytics.response_codes).map(
                  ([code, count]) => (
                    <div
                      key={code}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-3">
                        <StatusBadge
                          status={
                            code.startsWith("2")
                              ? "success"
                              : code.startsWith("4")
                              ? "warning"
                              : "error"
                          }
                          text={code}
                        />
                        <span className="text-sm text-gray-600">
                          {code.startsWith("2")
                            ? "Success"
                            : code.startsWith("4")
                            ? "Client Error"
                            : code.startsWith("5")
                            ? "Server Error"
                            : "Other"}
                        </span>
                      </div>
                      <span className="font-semibold text-gray-900">
                        {count}
                      </span>
                    </div>
                  )
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No response code data available
              </p>
            )}
          </div>
        </div>

        {/* Service Health */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Service Health Overview</h2>
          </div>
          <div className="p-6">
            {analytics?.log_analytics?.services ? (
              <div className="space-y-4">
                {Object.entries(analytics.log_analytics.services).map(
                  ([service, data]) => (
                    <div
                      key={service}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900 capitalize">
                          {service}
                        </h3>
                        <StatusBadge
                          status={data.errors > 0 ? "warning" : "success"}
                          text={data.errors > 0 ? "Issues" : "Healthy"}
                        />
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Requests:</span>
                          <div className="font-semibold">
                            {data.total_requests}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-500">Errors:</span>
                          <div className="font-semibold text-red-600">
                            {data.errors}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-500">Avg Latency:</span>
                          <div className="font-semibold">
                            {data.avg_latency
                              ? `${data.avg_latency.toFixed(1)}ms`
                              : "N/A"}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No service data available
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Time Series Analysis */}
      {analytics?.log_analytics?.time_series && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Time Series Analysis</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(analytics.log_analytics.time_series).map(
                ([window, data]) => (
                  <div
                    key={window}
                    className="text-center p-4 bg-gray-50 rounded-lg"
                  >
                    <h3 className="font-semibold text-gray-900 capitalize mb-2">
                      {window.replace(/_/g, " ")}
                    </h3>
                    <div className="space-y-2">
                      <div>
                        <span className="text-sm text-gray-500">
                          Total Requests:
                        </span>
                        <div className="text-xl font-bold text-gray-900">
                          {data.total}
                        </div>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Errors:</span>
                        <div className="text-lg font-semibold text-red-600">
                          {data.errors}
                        </div>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">
                          Error Rate:
                        </span>
                        <div className="text-lg font-semibold">
                          {data.total > 0
                            ? `${((data.errors / data.total) * 100).toFixed(
                                1
                              )}%`
                            : "0%"}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
