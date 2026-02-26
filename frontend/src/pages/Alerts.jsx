import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAlerts, acknowledgeAlert } from "../services/api.js";
import Loader from "../components/Loader.jsx";

const alertTypeStyles = {
  status_change: "border-neon-blue/40 bg-neon-blue/10 text-neon-blue",
  threat_increase: "border-neon-red/40 bg-neon-red/10 text-neon-red",
  content_change: "border-neon-yellow/40 bg-neon-yellow/10 text-neon-yellow",
  malware_detected: "border-red-500/40 bg-red-500/10 text-red-500",
  ioc_reuse: "border-purple-500/40 bg-purple-500/10 text-purple-500",
  default: "border-gray-500/40 bg-gray-500/10 text-gray-400"
};

const alertTypeLabels = {
  status_change: "Status Change",
  threat_increase: "Threat Increase",
  content_change: "Content Changed",
  malware_detected: "Malware Detected",
  ioc_reuse: "IOC Reuse",
  default: "Alert"
};

export default function Alerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all"); // all, unread, acknowledged

  useEffect(() => {
    loadAlerts(true); // Initial load with loading state
    // Refresh alerts every 30 seconds
    const interval = setInterval(() => {
      loadAlerts(false); // Background refresh without loading state
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleViewInDashboard = (url, alert) => {
    // Navigate to dashboard with the URL and alert context
    navigate("/?scanUrl=" + encodeURIComponent(url), {
      state: { alertData: alert }
    });
  };

  const loadAlerts = async (showLoading = true) => {
    if (showLoading) {
      setIsLoading(true);
    }
    setError("");
    try {
      const data = await getAlerts();
      setAlerts(data.alerts || []);
    } catch (err) {
      setError("Failed to load alerts. Please try again.");
      console.error(err);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      // Update local state
      setAlerts(alerts.map(alert => 
        alert._id === alertId 
          ? { ...alert, status: "acknowledged" } 
          : alert
      ));
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return "Unknown";
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-IN', { 
        timeZone: 'Asia/Kolkata',
        dateStyle: 'medium',
        timeStyle: 'short'
      });
    } catch {
      return isoString;
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === "all") return true;
    if (filter === "unread") return alert.status !== "acknowledged";
    if (filter === "acknowledged") return alert.status === "acknowledged";
    return true;
  });

  const unreadCount = alerts.filter(a => a.status !== "acknowledged").length;

  return (
    <div className="min-h-screen px-6 py-12 lg:px-16">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Alert Center</p>
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold md:text-4xl">Monitoring Alerts</h1>
            <button
              onClick={() => loadAlerts(false)}
              className="rounded-lg border border-neon-green/40 bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green hover:bg-neon-green/20 transition-colors"
            >
              Refresh
            </button>
          </div>
          <p className="text-sm text-gray-400">
            Real-time alerts from your monitored dark web sites. {unreadCount > 0 && (
              <span className="text-neon-yellow">({unreadCount} unread)</span>
            )}
          </p>
        </header>

        {/* Filter Tabs */}
        <div className="flex gap-2 border-b border-white/10 pb-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filter === "all"
                ? "border-b-2 border-neon-green text-neon-green"
                : "text-gray-400 hover:text-gray-300"
            }`}
          >
            All ({alerts.length})
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filter === "unread"
                ? "border-b-2 border-neon-yellow text-neon-yellow"
                : "text-gray-400 hover:text-gray-300"
            }`}
          >
            Unread ({unreadCount})
          </button>
          <button
            onClick={() => setFilter("acknowledged")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              filter === "acknowledged"
                ? "border-b-2 border-neon-blue text-neon-blue"
                : "text-gray-400 hover:text-gray-300"
            }`}
          >
            Acknowledged ({alerts.filter(a => a.status === "acknowledged").length})
          </button>
        </div>

        {isLoading && (
          <div className="flex min-h-[50vh] items-center justify-center">
            <Loader />
          </div>
        )}

        {error && !isLoading && (
          <div className="rounded-lg border border-neon-red/40 bg-neon-red/10 p-4 text-neon-red">
            {error}
          </div>
        )}

        {!isLoading && !error && filteredAlerts.length === 0 && (
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
            <svg className="h-16 w-16 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <p className="text-gray-500">
              {filter === "all" && "No alerts yet."}
              {filter === "unread" && "No unread alerts."}
              {filter === "acknowledged" && "No acknowledged alerts."}
            </p>
          </div>
        )}

        {!isLoading && !error && filteredAlerts.length > 0 && (
          <div className="space-y-4">
            {filteredAlerts.map((alert) => {
              const alertType = alert.alert_type || "default";
              const typeStyle = alertTypeStyles[alertType] || alertTypeStyles.default;
              const typeLabel = alertTypeLabels[alertType] || alertTypeLabels.default;
              const isAcknowledged = alert.status === "acknowledged";

              return (
                <div
                  key={alert._id}
                  className={`rounded-xl border bg-gray-900/50 p-6 transition-all ${
                    isAcknowledged
                      ? "border-white/5 opacity-60"
                      : "border-white/10"
                  }`}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-start gap-3">
                        <span className={`rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${typeStyle}`}>
                          {typeLabel}
                        </span>
                        {isAcknowledged && (
                          <span className="rounded-full border border-neon-green/40 bg-neon-green/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-neon-green">
                            ✓ Acknowledged
                          </span>
                        )}
                      </div>

                      <div>
                        <p className="text-lg font-semibold text-gray-100">
                          {alert.message || "Alert notification"}
                        </p>
                        {alert.url && (
                          <p className="mt-2 break-words text-sm text-gray-400">
                            URL: <button onClick={() => handleViewInDashboard(alert.url, alert)} className="text-neon-blue hover:text-neon-blue/80 underline cursor-pointer">{alert.url}</button>
                          </p>
                        )}
                      </div>

                      <div className="grid gap-3 text-sm text-gray-400 sm:grid-cols-2">
                        {alert.threat_score !== undefined && (
                          <div>
                            <span className="text-xs uppercase tracking-wider text-gray-500">Current Threat Score</span>
                            <p className="mt-1 text-lg font-semibold text-neon-red">{alert.threat_score}</p>
                          </div>
                        )}
                        {alert.previous_score !== undefined && (
                          <div>
                            <span className="text-xs uppercase tracking-wider text-gray-500">Previous Threat Score</span>
                            <p className="mt-1 text-lg font-semibold text-gray-300">{alert.previous_score}</p>
                          </div>
                        )}
                        {alert.score_increase !== undefined && (
                          <div>
                            <span className="text-xs uppercase tracking-wider text-gray-500">Score Increase</span>
                            <p className="mt-1 text-lg font-semibold text-neon-yellow">+{alert.score_increase}</p>
                          </div>
                        )}
                        {alert.reason && (
                          <div>
                            <span className="text-xs uppercase tracking-wider text-gray-500">Reason</span>
                            <p className="mt-1 text-gray-300">{alert.reason}</p>
                          </div>
                        )}
                      </div>

                      <p className="text-xs text-gray-500">
                        {formatTimestamp(alert.timestamp)}
                      </p>
                    </div>

                    <div className="flex gap-2 sm:flex-col">
                      {alert.url && (
                        <button
                          onClick={() => handleViewInDashboard(alert.url, alert)}
                          className="rounded-lg border border-neon-blue/40 bg-neon-blue/10 px-4 py-2 text-sm font-medium text-neon-blue hover:bg-neon-blue/20 transition-colors"
                        >
                          View in Dashboard
                        </button>
                      )}
                      {!isAcknowledged && (
                        <button
                          onClick={() => handleAcknowledge(alert._id)}
                          className="rounded-lg border border-neon-green/40 bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green hover:bg-neon-green/20 transition-colors"
                        >
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
