import React, { useState, useEffect } from "react";
import {
  Bars3Icon,
  ArrowPathIcon,
  BellIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { apiService, dataUtils } from "../services/api";
import toast from "react-hot-toast";

const Header = ({ onMenuClick }) => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      const health = await apiService.getHealth();
      setSystemStatus(health);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch system status:", error);
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Manual refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetchSystemStatus();
      toast.success("Data refreshed successfully");
    } catch (error) {
      toast.error("Failed to refresh data");
    } finally {
      setIsRefreshing(false);
    }
  };

  // Get status icon and color
  const getStatusIcon = (status) => {
    switch (status) {
      case "healthy":
        return <CheckCircleIcon className="w-5 h-5 text-success-600" />;
      case "unhealthy":
        return <XCircleIcon className="w-5 h-5 text-danger-600" />;
      case "warning":
        return <ExclamationTriangleIcon className="w-5 h-5 text-warning-600" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "healthy":
        return "text-success-700 bg-success-50 border-success-200";
      case "unhealthy":
        return "text-danger-700 bg-danger-50 border-danger-200";
      case "warning":
        return "text-warning-700 bg-warning-50 border-warning-200";
      default:
        return "text-gray-700 bg-gray-50 border-gray-200";
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left side */}
        <div className="flex items-center">
          <button
            type="button"
            className="text-gray-400 hover:text-gray-600 lg:hidden"
            onClick={onMenuClick}
          >
            <Bars3Icon className="w-6 h-6" />
          </button>

          <div className="ml-4 lg:ml-0">
            <h1 className="text-xl font-semibold text-gray-900">
              Health Monitoring Dashboard
            </h1>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* System Status */}
          {systemStatus && (
            <div
              className={`flex items-center px-3 py-2 rounded-lg border ${getStatusColor(
                systemStatus.status
              )}`}
            >
              {getStatusIcon(systemStatus.status)}
              <span className="ml-2 text-sm font-medium capitalize">
                {systemStatus.status}
              </span>
            </div>
          )}

          {/* Component Status */}
          {systemStatus?.components && (
            <div className="hidden md:flex items-center space-x-2">
              {Object.entries(systemStatus.components).map(
                ([component, status]) => (
                  <div
                    key={component}
                    className={`flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                      status
                    )}`}
                    title={`${component}: ${status}`}
                  >
                    <div
                      className={`w-1.5 h-1.5 rounded-full mr-1 ${
                        status === "healthy"
                          ? "bg-success-500"
                          : status === "unhealthy"
                          ? "bg-danger-500"
                          : "bg-warning-500"
                      }`}
                    />
                    {component}
                  </div>
                )
              )}
            </div>
          )}

          {/* Metrics Summary */}
          {systemStatus?.metrics && (
            <div className="hidden lg:flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center">
                <span className="font-medium">Logs:</span>
                <span className="ml-1">
                  {dataUtils.formatNumber(systemStatus.metrics.total_logs)}
                </span>
              </div>
              <div className="flex items-center">
                <span className="font-medium">Errors:</span>
                <span className="ml-1">
                  {dataUtils.formatNumber(systemStatus.metrics.total_errors)}
                </span>
              </div>
              <div className="flex items-center">
                <span className="font-medium">Anomalies:</span>
                <span className="ml-1">
                  {dataUtils.formatNumber(
                    systemStatus.metrics.active_anomalies
                  )}
                </span>
              </div>
            </div>
          )}

          {/* Refresh Button */}
          <button
            type="button"
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
            onClick={handleRefresh}
            disabled={isRefreshing}
            title="Refresh data"
          >
            <ArrowPathIcon
              className={`w-5 h-5 ${isRefreshing ? "animate-spin" : ""}`}
            />
          </button>

          {/* Notifications */}
          <button
            type="button"
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
            title="Notifications"
          >
            <BellIcon className="w-5 h-5" />
          </button>

          {/* Last Updated */}
          <div className="hidden sm:flex items-center text-xs text-gray-500">
            <span>Updated: {lastUpdated.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
