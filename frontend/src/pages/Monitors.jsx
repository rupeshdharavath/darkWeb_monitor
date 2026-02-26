import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listMonitors, deleteMonitor, deleteAllMonitors, pauseMonitor, resumeMonitor, createMonitor } from "../services/api.js";
import Loader from "../components/Loader.jsx";
import { useToast } from "../hooks/useToast.jsx";

export default function Monitors() {
  const navigate = useNavigate();
  const { showToast, ToastContainer } = useToast();
  const [monitors, setMonitors] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newMonitorUrl, setNewMonitorUrl] = useState("");
  const [newMonitorInterval, setNewMonitorInterval] = useState(5);
  const [creating, setCreating] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [loadingStates, setLoadingStates] = useState({}); // Track loading for each button
  const [deletingAll, setDeletingAll] = useState(false);

  useEffect(() => {
    loadMonitors(true);
    // Refresh monitors every 10 seconds
    const interval = setInterval(() => {
      loadMonitors(false);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadMonitors = async (showLoading = false) => {
    if (showLoading) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }
    setError("");
    try {
      const data = await listMonitors();
      setMonitors(data.monitors || []);
      if (isInitialLoad) {
        setIsInitialLoad(false);
      }
    } catch (err) {
      setError("Failed to load monitors. Please try again.");
      console.error(err);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      } else {
        setIsRefreshing(false);
      }
    }
  };

  const handleCreateMonitor = async (e) => {
    e.preventDefault();
    if (!newMonitorUrl.trim()) return;

    // Check if max monitors limit reached (5)
    if (monitors.length >= 5) {
      showToast("Maximum 5 monitors allowed. Please delete an existing monitor to add a new one.", "warning");
      return;
    }

    setCreating(true);
    try {
      await createMonitor(newMonitorUrl.trim(), newMonitorInterval);
      setNewMonitorUrl("");
      setNewMonitorInterval(5);
      setShowCreateForm(false);
      showToast("Monitor created successfully!", "success");
      loadMonitors(false); // Refresh monitor list with animation
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || "Unknown error occurred";
      showToast("Failed to create monitor: " + errorMessage, "error");
      console.error("Monitor creation error:", err);
    } finally {
      setCreating(false);
    }
  };

  const handlePause = async (monitorId) => {
    setLoadingStates(prev => ({ ...prev, [`pause_${monitorId}`]: true }));
    try {
      await pauseMonitor(monitorId);
      showToast("Monitor paused successfully", "success");
      loadMonitors(false); // Refresh monitor list with animation
    } catch (err) {
      showToast("Failed to pause monitor: " + (err.response?.data?.detail || err.message), "error");
    } finally {
      setLoadingStates(prev => ({ ...prev, [`pause_${monitorId}`]: false }));
    }
  };

  const handleResume = async (monitorId) => {
    setLoadingStates(prev => ({ ...prev, [`resume_${monitorId}`]: true }));
    try {
      await resumeMonitor(monitorId);
      showToast("Monitor resumed successfully", "success");
      loadMonitors(false); // Refresh monitor list with animation
    } catch (err) {
      showToast("Failed to resume monitor: " + (err.response?.data?.detail || err.message), "error");
    } finally {
      setLoadingStates(prev => ({ ...prev, [`resume_${monitorId}`]: false }));
    }
  };

  const handleDelete = async (monitorId) => {
    if (!confirm("Are you sure you want to delete this monitor?")) return;
    
    setLoadingStates(prev => ({ ...prev, [`delete_${monitorId}`]: true }));
    try {
      await deleteMonitor(monitorId);
      showToast("Monitor deleted successfully", "success");
      loadMonitors(false); // Refresh monitor list with animation
    } catch (err) {
      showToast("Failed to delete monitor: " + (err.response?.data?.detail || err.message), "error");
    } finally {
      setLoadingStates(prev => ({ ...prev, [`delete_${monitorId}`]: false }));
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm(`Are you sure you want to delete all ${monitors.length} monitors? This action cannot be undone.`)) return;
    
    setDeletingAll(true);
    try {
      await deleteAllMonitors();
      showToast("All monitors deleted successfully", "success");
      loadMonitors(false); // Refresh monitor list with animation
    } catch (err) {
      showToast("Failed to delete all monitors: " + (err.response?.data?.detail || err.message), "error");
    } finally {
      setDeletingAll(false);
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return "Not scanned yet";
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-IN', { 
        timeZone: 'Asia/Kolkata',
        dateStyle: 'short',
        timeStyle: 'short'
      });
    } catch {
      return isoString;
    }
  };

  const handleViewInDashboard = (url) => {
    // Navigate to dashboard with the URL
    navigate(`/?scanUrl=${encodeURIComponent(url)}`);
  };

  const getNextScanTime = (lastScan, interval) => {
    if (!lastScan) return "Pending initial scan";
    try {
      const lastDate = new Date(lastScan);
      const nextDate = new Date(lastDate.getTime() + interval * 60 * 1000);
      const now = new Date();
      
      if (nextDate <= now) return "Scanning soon...";
      
      const diffMs = nextDate - now;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return "Less than 1 minute";
      if (diffMins === 1) return "In 1 minute";
      return `In ${diffMins} minutes`;
    } catch {
      return "Unknown";
    }
  };

  return (
    <div className="min-h-screen px-6 py-12 lg:px-16">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Monitor Management</p>
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold md:text-4xl">Active Monitors</h1>
            <div className="flex gap-3">
              <button
                onClick={() => loadMonitors(false)}
                disabled={isRefreshing}
                className="rounded-lg border border-neon-blue/40 bg-neon-blue/10 px-4 py-2 text-sm font-medium text-neon-blue hover:bg-neon-blue/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isRefreshing && (
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
              </button>
              {monitors.length > 0 && (
                <button
                  onClick={handleDeleteAll}
                  disabled={deletingAll}
                  className="rounded-lg border border-neon-red/40 bg-neon-red/10 px-4 py-2 text-sm font-medium text-neon-red hover:bg-neon-red/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {deletingAll && (
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  <span>{deletingAll ? "Deleting..." : "Delete All"}</span>
                </button>
              )}
              <button
                onClick={() => setShowCreateForm(!showCreateForm)}
                disabled={monitors.length >= 5 && !showCreateForm}
                className="rounded-lg border border-neon-green/40 bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green hover:bg-neon-green/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {showCreateForm ? "Cancel" : "+ New Monitor"}
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-400">
            Manage automated monitoring of dark web sites. Currently monitoring {monitors.length}/5 site{monitors.length !== 1 ? 's' : ''}.
            {monitors.length >= 5 && <span className="text-neon-yellow ml-2">(Maximum reached)</span>}
          </p>
        </header>

        {/* Create Monitor Form */}
        {showCreateForm && (
          <div className="rounded-xl border border-neon-green/40 bg-gray-900/60 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-neon-green">Create New Monitor</h2>
              <span className="text-xs text-gray-400">{monitors.length}/5 monitors</span>
            </div>
            {monitors.length >= 5 && (
              <div className="mb-4 rounded-lg border border-neon-yellow/40 bg-neon-yellow/10 p-3 text-sm text-neon-yellow">
                ⚠️ Maximum monitor limit reached. Delete an existing monitor to add a new one.
              </div>
            )}
            <form onSubmit={handleCreateMonitor} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">URL to Monitor</label>
                <input
                  type="text"
                  value={newMonitorUrl}
                  onChange={(e) => setNewMonitorUrl(e.target.value)}
                  placeholder="https://example.onion or http://..."
                  className="w-full rounded-lg border border-white/10 bg-gray-900/60 px-4 py-3 text-base text-gray-100 outline-none transition focus:border-neon-green/70 focus:ring-2 focus:ring-neon-green/30"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Scan Interval (minutes)</label>
                <input
                  type="number"
                  value={newMonitorInterval}
                  onChange={(e) => setNewMonitorInterval(parseInt(e.target.value) || 5)}
                  min="1"
                  max="1440"
                  className="w-full rounded-lg border border-white/10 bg-gray-900/60 px-4 py-3 text-base text-gray-100 outline-none transition focus:border-neon-green/70 focus:ring-2 focus:ring-neon-green/30"
                />
                <p className="mt-1 text-xs text-gray-500">Minimum: 1 minute, Maximum: 1440 minutes (24 hours)</p>
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={creating || !newMonitorUrl.trim()}
                  className="rounded-lg border border-neon-green/40 bg-neon-green/20 px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] text-neon-green transition hover:bg-neon-green/30 disabled:cursor-not-allowed disabled:opacity-50 flex items-center gap-2"
                >
                  {creating && (
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  <span>{creating ? "Creating..." : "Create Monitor"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewMonitorUrl("");
                    setNewMonitorInterval(5);
                  }}
                  className="rounded-lg border border-gray-500/40 bg-gray-500/10 px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] text-gray-400 transition hover:bg-gray-500/20"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {isLoading && monitors.length === 0 && (
          <div className="flex min-h-[50vh] items-center justify-center">
            <Loader />
          </div>
        )}

        {error && !isLoading && (
          <div className="rounded-lg border border-neon-red/40 bg-neon-red/10 p-4 text-neon-red">
            {error}
          </div>
        )}

        {!isLoading && !error && monitors.length === 0 && (
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
            <svg className="h-16 w-16 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-500">No active monitors yet.</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-2 rounded-lg bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green border border-neon-green/30 hover:bg-neon-green/20 transition-colors"
            >
              Create First Monitor
            </button>
          </div>
        )}

        {!isLoading && !error && monitors.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2">
            {monitors.map((monitor) => {
              const isPaused = monitor.paused || false;
              const isActive = !isPaused;

              return (
                <div
                  key={monitor.monitor_id || monitor.url}
                  className="rounded-xl border border-white/10 bg-gray-900/50 p-6 transition-all hover:border-white/20"
                >
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`inline-flex h-3 w-3 rounded-full ${isActive ? 'bg-neon-green animate-pulse' : 'bg-gray-500'}`}></span>
                          <span className={`text-xs uppercase tracking-[0.2em] ${isActive ? 'text-neon-green' : 'text-gray-500'}`}>
                            {isActive ? 'Active' : 'Paused'}
                          </span>
                        </div>
                        <button 
                          onClick={() => handleViewInDashboard(monitor.url)}
                          className="w-full text-left break-all text-sm font-mono text-neon-blue hover:text-neon-blue/80 hover:underline cursor-pointer transition-colors bg-gray-900/30 px-3 py-2 rounded border border-white/5 hover:border-neon-blue/30"
                        >
                          {monitor.url}
                        </button>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500">Interval</p>
                        <p className="mt-1 text-gray-300">{monitor.interval} min</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500">Scan Count</p>
                        <p className="mt-1 text-gray-300">{monitor.scan_count || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500">Last Scan</p>
                        <p className="mt-1 text-xs text-gray-300">{formatTimestamp(monitor.last_scan)}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500">Next Scan</p>
                        <p className="mt-1 text-xs text-gray-300">
                          {isPaused ? "Paused" : getNextScanTime(monitor.last_scan, monitor.interval)}
                        </p>
                      </div>
                    </div>

                    {/* Monitor ID */}
                    {monitor.monitor_id && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500">Monitor ID</p>
                        <p className="mt-1 font-mono text-xs text-gray-400 break-all">{monitor.monitor_id}</p>
                      </div>
                    )}

                    {/* Created At */}
                    {monitor.created_at && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500">Created</p>
                        <p className="mt-1 text-xs text-gray-400">{formatTimestamp(monitor.created_at)}</p>
                      </div>
                    )}

                    {/* Last Scan Details */}
                    {monitor.last_scan_data && (
                      <div className="rounded-lg border border-neon-blue/30 bg-neon-blue/5 p-4">
                        <p className="text-xs uppercase tracking-wider text-neon-blue mb-3">Last Scan Results</p>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-xs text-gray-500">Status</p>
                            <p className={`mt-1 text-xs font-semibold ${
                              monitor.last_scan_data.status === 'ONLINE' ? 'text-neon-green' :
                              monitor.last_scan_data.status === 'OFFLINE' ? 'text-neon-red' :
                              'text-gray-400'
                            }`}>
                              {monitor.last_scan_data.status}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Threat Score</p>
                            <p className={`mt-1 text-xs font-semibold ${
                              monitor.last_scan_data.threat_score >= 70 ? 'text-neon-red' :
                              monitor.last_scan_data.threat_score >= 40 ? 'text-neon-yellow' :
                              'text-neon-green'
                            }`}>
                              {monitor.last_scan_data.threat_score}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Risk Level</p>
                            <p className="mt-1 text-xs text-gray-300">{monitor.last_scan_data.risk_level}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Category</p>
                            <p className="mt-1 text-xs text-gray-300">{monitor.last_scan_data.category}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">IOCs Found</p>
                            <p className="mt-1 text-xs text-gray-300">
                              {monitor.last_scan_data.emails_count + monitor.last_scan_data.urls_count + 
                               monitor.last_scan_data.ips_count + monitor.last_scan_data.crypto_count}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Malware</p>
                            <p className={`mt-1 text-xs font-semibold ${
                              monitor.last_scan_data.clamav_detected ? 'text-neon-red' : 'text-neon-green'
                            }`}>
                              {monitor.last_scan_data.clamav_detected ? 'Detected' : 'Clean'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-white/10">
                      {isActive ? (
                        <button
                          onClick={() => handlePause(monitor.monitor_id)}
                          disabled={loadingStates[`pause_${monitor.monitor_id}`]}
                          className="flex-1 rounded-lg border border-neon-yellow/40 bg-neon-yellow/10 px-4 py-2 text-sm font-medium text-neon-yellow hover:bg-neon-yellow/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          {loadingStates[`pause_${monitor.monitor_id}`] && (
                            <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          )}
                          <span>{loadingStates[`pause_${monitor.monitor_id}`] ? "Pausing..." : "Pause"}</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleResume(monitor.monitor_id)}
                          disabled={loadingStates[`resume_${monitor.monitor_id}`]}
                          className="flex-1 rounded-lg border border-neon-green/40 bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green hover:bg-neon-green/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          {loadingStates[`resume_${monitor.monitor_id}`] && (
                            <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          )}
                          <span>{loadingStates[`resume_${monitor.monitor_id}`] ? "Resuming..." : "Resume"}</span>
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(monitor.monitor_id)}
                        disabled={loadingStates[`delete_${monitor.monitor_id}`]}
                        className="flex-1 rounded-lg border border-neon-red/40 bg-neon-red/10 px-4 py-2 text-sm font-medium text-neon-red hover:bg-neon-red/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        {loadingStates[`delete_${monitor.monitor_id}`] && (
                          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        )}
                        <span>{loadingStates[`delete_${monitor.monitor_id}`] ? "Deleting..." : "Delete"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      <ToastContainer />
    </div>
  );
}
