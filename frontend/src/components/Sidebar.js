import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  HomeIcon,
  ServerIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  XMarkIcon,
  CheckCircleIcon,
  ClockIcon,
  CpuChipIcon,
} from "@heroicons/react/24/outline";
import { clsx } from "clsx";

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: HomeIcon,
    description: "System overview",
  },
  {
    name: "Services",
    href: "/services",
    icon: ServerIcon,
    description: "Service health",
  },
  {
    name: "Logs",
    href: "/logs",
    icon: DocumentTextIcon,
    description: "Recent logs",
  },
  {
    name: "Metrics",
    href: "/metrics",
    icon: ChartBarIcon,
    description: "Prometheus metrics",
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: CogIcon,
    description: "Advanced analytics",
  },
];

const Sidebar = ({ open, setOpen }) => {
  const location = useLocation();

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <CheckCircleIcon className="w-5 h-5 text-white" />
                </div>
                <div className="ml-3">
                  <h1 className="text-lg font-semibold text-gray-900">
                    Health Monitor
                  </h1>
                </div>
              </div>
            </div>
          </div>
          <div className="lg:hidden">
            <button
              type="button"
              className="text-gray-400 hover:text-gray-600"
              onClick={() => setOpen(false)}
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200",
                  isActive
                    ? "bg-primary-50 text-primary-700 border-r-2 border-primary-600"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
                onClick={() => setOpen(false)}
              >
                <item.icon
                  className={clsx(
                    "mr-3 h-5 w-5 flex-shrink-0",
                    isActive
                      ? "text-primary-600"
                      : "text-gray-400 group-hover:text-gray-500"
                  )}
                />
                <div className="flex-1">
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-gray-500">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Status indicators */}
        <div className="border-t border-gray-200 p-4">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              System Status
            </h3>

            {/* Quick status indicators */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Overall Health</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                  <span className="text-success-700 font-medium">Healthy</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Services</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                  <span className="text-success-700 font-medium">3/3</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Prometheus</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-warning-500 rounded-full mr-2"></div>
                  <span className="text-warning-700 font-medium">Warning</span>
                </div>
              </div>
            </div>

            {/* Last updated */}
            <div className="flex items-center text-xs text-gray-500">
              <ClockIcon className="w-3 h-3 mr-1" />
              <span>Updated just now</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
