import axios from "axios";
import toast from "react-hot-toast";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Response Error:", error);

    const message =
      error.response?.data?.detail || error.message || "An error occurred";

    // Show toast notification for errors
    if (error.response?.status >= 500) {
      toast.error(`Server Error: ${message}`);
    } else if (error.response?.status >= 400) {
      toast.error(`Request Error: ${message}`);
    } else if (error.code === "ECONNABORTED") {
      toast.error("Request timeout. Please try again.");
    } else {
      toast.error(`Network Error: ${message}`);
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const API_ENDPOINTS = {
  // Health & Status
  HEALTH: "/api/health",
  SUMMARY: "/api/summary",

  // Metrics & Analytics
  METRICS: "/api/metrics",
  PERFORMANCE: "/api/performance",
  ANALYTICS: "/api/analytics",

  // Logs
  LOGS: "/api/logs",

  // Error Analysis
  ERROR_ANALYSIS: "/api/errors/analysis",
  ROOT_CAUSE: "/api/root_cause",

  // Prometheus
  PROMETHEUS_STATUS: "/api/prometheus/status",

  // Ollama
  OLLAMA_TEST: "/api/ollama/test",
};

// API service functions
export const apiService = {
  // Health & Status
  async getHealth() {
    const response = await api.get(API_ENDPOINTS.HEALTH);
    return response.data;
  },

  async getSummary() {
    const response = await api.get(API_ENDPOINTS.SUMMARY);
    return response.data;
  },

  // Metrics & Analytics
  async getMetrics() {
    const response = await api.get(API_ENDPOINTS.METRICS);
    return response.data;
  },

  async getPerformance() {
    const response = await api.get(API_ENDPOINTS.PERFORMANCE);
    return response.data;
  },

  async getAnalytics() {
    const response = await api.get(API_ENDPOINTS.ANALYTICS);
    return response.data;
  },

  // Logs
  async getLogs() {
    const response = await api.get(API_ENDPOINTS.LOGS);
    return response.data;
  },

  // Error Analysis
  async getErrorAnalysis() {
    const response = await api.get(API_ENDPOINTS.ERROR_ANALYSIS);
    return response.data;
  },

  async getRootCause() {
    const response = await api.get(API_ENDPOINTS.ROOT_CAUSE);
    return response.data;
  },

  // Prometheus
  async getPrometheusStatus() {
    const response = await api.get(API_ENDPOINTS.PROMETHEUS_STATUS);
    return response.data;
  },

  // Ollama
  async testOllama() {
    const response = await api.get(API_ENDPOINTS.OLLAMA_TEST);
    return response.data;
  },

  // Prometheus direct queries (for advanced metrics)
  async queryPrometheus(query) {
    const response = await axios.get(`http://localhost:9090/api/v1/query`, {
      params: { query },
      timeout: 5000,
    });
    return response.data;
  },

  // Get Prometheus targets
  async getPrometheusTargets() {
    const response = await axios.get(`http://localhost:9090/api/v1/targets`, {
      timeout: 5000,
    });
    return response.data;
  },

  // Services
  async getServices() {
    const response = await api.get("/api/services");
    return response.data;
  },
};

// Utility functions for data processing
export const dataUtils = {
  // Format status for display
  formatStatus(status) {
    const statusMap = {
      healthy: { label: "Healthy", color: "success", icon: "✓" },
      unhealthy: { label: "Unhealthy", color: "error", icon: "✗" },
      warning: { label: "Warning", color: "warning", icon: "⚠" },
      unknown: { label: "Unknown", color: "gray", icon: "?" },
    };
    return statusMap[status] || statusMap.unknown;
  },

  // Format numbers for display
  formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return "N/A";
    if (typeof num === "string") return num;

    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(decimals)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(decimals)}K`;
    } else {
      return num.toFixed(decimals);
    }
  },

  // Format percentage
  formatPercentage(value, total) {
    if (!total || total === 0) return "0%";
    return `${((value / total) * 100).toFixed(1)}%`;
  },

  // Format duration
  formatDuration(seconds) {
    if (!seconds) return "N/A";

    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    } else if (seconds < 60) {
      return `${seconds.toFixed(2)}s`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
    }
  },

  // Get color for metric values
  getMetricColor(value, thresholds = { warning: 80, error: 95 }) {
    if (value >= thresholds.error) return "danger";
    if (value >= thresholds.warning) return "warning";
    return "success";
  },

  // Parse log level for styling
  getLogLevelColor(level) {
    const levelMap = {
      error: "danger",
      warning: "warning",
      info: "primary",
      debug: "gray",
    };
    return levelMap[level?.toLowerCase()] || "gray";
  },

  // Format timestamp for display
  formatTimestamp(timestamp) {
    if (!timestamp) return "N/A";

    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);

      if (diffMins < 1) {
        return "Just now";
      } else if (diffMins < 60) {
        return `${diffMins}m ago`;
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else {
        return date.toLocaleString();
      }
    } catch (error) {
      return timestamp;
    }
  },
};

export default api;
