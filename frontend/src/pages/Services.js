import React, { useState, useEffect } from "react";
import {
  ServerIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  ChartBarIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { apiService, dataUtils } from "../services/api";
import StatusBadge, { StatusPulse } from "../components/StatusBadge";
import MetricCard from "../components/MetricCard";
import toast from "react-hot-toast";

const Services = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Fetch service data from /api/services
  const fetchServiceData = async () => {
    try {
      setLoading(true);
      const res = await apiService.getServices();
      setServices(res.services || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch service data:", error);
      toast.error("Failed to load service data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServiceData();
    const interval = setInterval(fetchServiceData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Manual refresh
  const handleRefresh = () => {
    fetchServiceData();
    toast.success("Service data refreshed");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Service Health</h1>
          <p className="text-gray-600">
            Monitor individual service status and performance
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          <button
            onClick={handleRefresh}
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

      {/* Service Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {services.map((service) => (
          <div key={service.name} className="card">
            {/* Service Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <ServerIcon className="w-6 h-6 text-primary-600" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {service.displayName ||
                      service.name.replace("_", " ").toUpperCase()}
                  </h3>
                  <p className="text-sm text-gray-500">{service.name}</p>
                </div>
              </div>
              <StatusPulse status={service.status} />
            </div>

            {/* Service Metrics */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <MetricCard
                title="Uptime"
                value={
                  service.uptime !== null ? `${service.uptime} min` : "N/A"
                }
                subtitle="Minutes"
                icon={ClockIcon}
                color="primary"
                loading={loading}
              />
              <MetricCard
                title="Avg Latency"
                value={
                  service.avg_latency !== null
                    ? `${service.avg_latency} ms`
                    : "N/A"
                }
                subtitle="Avg Response"
                icon={ChartBarIcon}
                color={
                  service.avg_latency > 500
                    ? "danger"
                    : service.avg_latency > 200
                    ? "warning"
                    : "success"
                }
                loading={loading}
              />
              <MetricCard
                title="Memory"
                value={
                  service.memory_mb !== null ? `${service.memory_mb} MB` : "N/A"
                }
                subtitle="Memory Usage"
                icon={CpuChipIcon}
                color={
                  service.memory_mb > 500
                    ? "danger"
                    : service.memory_mb > 200
                    ? "warning"
                    : "success"
                }
                loading={loading}
              />
              <MetricCard
                title="CPU"
                value={
                  service.cpu_percent !== null
                    ? `${service.cpu_percent}%`
                    : "N/A"
                }
                subtitle="CPU Usage"
                icon={CpuChipIcon}
                color={
                  service.cpu_percent > 80
                    ? "danger"
                    : service.cpu_percent > 50
                    ? "warning"
                    : "success"
                }
                loading={loading}
              />
              <MetricCard
                title="Error Rate"
                value={`${service.error_rate}%`}
                subtitle="Errors"
                icon={ExclamationTriangleIcon}
                color={
                  service.error_rate > 5
                    ? "danger"
                    : service.error_rate > 1
                    ? "warning"
                    : "success"
                }
                loading={loading}
              />
              <MetricCard
                title="Requests"
                value={service.total_requests}
                subtitle="Total"
                icon={ChartBarIcon}
                color="primary"
                loading={loading}
              />
              <MetricCard
                title="Errors"
                value={service.errors}
                subtitle="Total"
                icon={ExclamationTriangleIcon}
                color={service.errors > 0 ? "danger" : "success"}
                loading={loading}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Services;
