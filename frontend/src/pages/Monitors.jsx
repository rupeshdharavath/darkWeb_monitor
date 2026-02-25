import { useState, useEffect } from "react";
import { createMonitor, listMonitors, deleteMonitor, scanOnion, getAlerts } from "../services/api.js";
import Loader from "../components/Loader.jsx";

const riskStyles = {
  LOW: "bg-neon-green/15 text-neon-green border-neon-green/40",
  MEDIUM: "bg-neon-yellow/15 text-neon-yellow border-neon-yellow/40",
  HIGH: "bg-neon-red/15 text-neon-red border-neon-red/40"
};

export default function Monitors() {
  const [tabs, setTabs] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [monitors, setMonitors] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [showAlerts, setShowAlerts] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadMonitors();
    loadAlerts();
    
    // Refresh alerts every 30 seconds
    const interval = setInterval(() => {
      loadAlerts();
      refreshTabData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadMonitors = async () => {
    try {
      const data = await listMonitors();
      setMonitors(data.monitors || {});
    } catch (err) {
      console.error("Failed to load monitors:", err);
    }
  };

  const loadAlerts = async () => {
    try {
      const data = await getAlerts();
      // Filter only new alerts
      const newAlerts = (data.alerts || []).filter(a => a.status === "new");
      setAlerts(newAlerts);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    }
  };

  const refreshTabData = () => {
    tabs.forEach((tab, index) => {
      if (tab.scanResult && tab.url) {
        handleScan(tab.url, index, true); // Silent refresh
      }
    });
  };

  const addTab = () => {
    if (tabs.length >= 10) {
      alert("Maximum 10 tabs allowed");
      return;
    }
    
    const newTab = {
      id: Date.now(),
      url: "",
      scanResult: null,
      isLoading: false,
      error: "",
      monitorId: null,
      isMonitoring: false
    };
    
    setTabs([...tabs, newTab]);
    setActiveTab(tabs.length);
  };

  const closeTab = async (index) => {
    const tab = tabs[index];
    
    // Remove monitor if active
    if (tab.monitorId) {
      try {
        await deleteMonitor(tab.monitorId);
      } catch (err) {
        console.error("Failed to delete monitor:", err);
      }
    }
    
    const newTabs = tabs.filter((_, i) => i !== index);
    setTabs(newTabs);
    if (activeTab >= newTabs.length && newTabs.length > 0) {
      setActiveTab(newTabs.length - 1);
    } else if (newTabs.length === 0) {
      setActiveTab(0);
    }
  };

  const handleScan = async (url, tabIndex, silent = false) => {
    if (!url) return;

    const updatedTabs = [...tabs];
    updatedTabs[tabIndex].isLoading = true;
    updatedTabs[tabIndex].error = "";
    setTabs(updatedTabs);

    try {
      const data = await scanOnion(url);
      updatedTabs[tabIndex].scanResult = data;
      updatedTabs[tabIndex].url = url;
      updatedTabs[tabIndex].isLoading = false;
      setTabs(updatedTabs);
    } catch (err) {
      if (!silent) {
        updatedTabs[tabIndex].error = "Scan failed. Check URL or API.";
        updatedTabs[tabIndex].isLoading = false;
        setTabs(updatedTabs);
      }
    }
  };

  const toggleMonitoring = async (tabIndex) => {
    const tab = tabs[tabIndex];
    
    if (tab.isMonitoring) {
      // Stop monitoring
      try {
        await deleteMonitor(tab.monitorId);
        const updatedTabs = [...tabs];
        updatedTabs[tabIndex].isMonitoring = false;
        updatedTabs[tabIndex].monitorId = null;
        setTabs(updatedTabs);
        loadMonitors();
      } catch (err) {
        console.error("Failed to stop monitoring:", err);
      }
    } else {
      // Start monitoring
      if (!tab.url) {
        alert("Please scan a URL first");
        return;
      }
      
      try {
        const data = await createMonitor(tab.url, 5);
        const updatedTabs = [...tabs];
        updatedTabs[tabIndex].isMonitoring = true;
        updatedTabs[tabIndex].monitorId = data.monitor_id;
        setTabs(updatedTabs);
        loadMonitors();
      } catch (err) {
        console.error("Failed to start monitoring:", err);
        alert("Failed to start monitoring");
      }
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return "Unknown";
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

  const getThreatColor = (score) => {
    if (score >= 70) return "text-neon-red";
    if (score >= 40) return "text-neon-yellow";
    return "text-neon-green";
  };

  // Initialize with one tab if empty
  useEffect(() => {
    if (tabs.length === 0) {
      addTab();
    }
  }, []);

  const currentTab = tabs[activeTab];

  return (
    <div className="min-h-screen px-6 py-6 lg:px-16">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        {/* Header */}
        <header className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Active Monitoring</p>
              <h1 className="text-3xl font-semibold md:text-4xl">Multi-Tab Scanner</h1>
              <p className="mt-2 text-sm text-gray-400">
                Monitor up to 10 onion sites simultaneously with auto-refresh every 5 minutes
              </p>
            </div>
            <button
              onClick={() => setShowAlerts(!showAlerts)}
              className="relative rounded-lg bg-neon-red/10 px-4 py-2 text-sm font-medium text-neon-red border border-neon-red/30 hover:bg-neon-red/20 transition-colors"
            >
              🚨 Alerts {alerts.length > 0 && `(${alerts.length})`}
              {alerts.length > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-neon-red text-xs text-white">
                  {alerts.length}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* Alerts Panel */}
        {showAlerts && (
          <div className="rounded-lg border border-neon-red/40 bg-neon-red/10 p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-neon-red">Recent Alerts</h3>
              <button
                onClick={() => setShowAlerts(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
              {alerts.length === 0 ? (
                <p className="text-sm text-gray-400">No new alerts</p>
              ) : (
                alerts.map((alert) => (
                  <div key={alert._id} className="rounded-lg border border-neon-red/30 bg-black/20 p-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-neon-red">{alert.reason}</p>
                        <p className="mt-1 text-xs text-gray-400 break-all">{alert.url}</p>
                        <div className="mt-2 flex gap-3 text-xs text-gray-500">
                          <span>Score: {alert.previous_score} → {alert.threat_score} (+{alert.score_increase})</span>
                          <span>•</span>
                          <span>{formatTimestamp(alert.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-2 border-b border-white/10 overflow-x-auto pb-2">
          {tabs.map((tab, index) => (
            <div
              key={tab.id}
              className={`flex items-center gap-2 rounded-t-lg border-x border-t px-4 py-2 transition-colors ${
                activeTab === index
                  ? "border-neon-green/40 bg-gray-900 text-white"
                  : "border-white/10 bg-white/5 text-gray-400 hover:bg-white/10"
              }`}
            >
              <button
                onClick={() => setActiveTab(index)}
                className="text-sm font-medium min-w-[80px] text-left"
              >
                {tab.scanResult?.title || `Tab ${index + 1}`}
              </button>
              {tab.isMonitoring && (
                <span className="text-xs text-neon-green">●</span>
              )}
              {tabs.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(index);
                  }}
                  className="text-gray-500 hover:text-white"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          {tabs.length < 10 && (
            <button
              onClick={addTab}
              className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-400 hover:bg-white/10 hover:text-white"
            >
              + New Tab
            </button>
          )}
        </div>

        {/* Current Tab Content */}
        {currentTab && (
          <div className="flex flex-col gap-6">
            {/* Search Bar */}
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Enter .onion URL"
                value={currentTab.url || ""}
                onChange={(e) => {
                  const updatedTabs = [...tabs];
                  updatedTabs[activeTab].url = e.target.value;
                  setTabs(updatedTabs);
                }}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    handleScan(currentTab.url, activeTab);
                  }
                }}
                className="flex-1 rounded-lg border border-white/10 bg-gray-900 px-4 py-3 text-white placeholder-gray-500 focus:border-neon-green/40 focus:outline-none"
              />
              <button
                onClick={() => handleScan(currentTab.url, activeTab)}
                disabled={currentTab.isLoading || !currentTab.url}
                className="rounded-lg bg-neon-green/10 px-6 py-3 font-medium text-neon-green border border-neon-green/30 hover:bg-neon-green/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {currentTab.isLoading ? "Scanning..." : "Scan"}
              </button>
              <button
                onClick={() => toggleMonitoring(activeTab)}
                disabled={!currentTab.scanResult}
                className={`rounded-lg px-6 py-3 font-medium border transition-colors ${
                  currentTab.isMonitoring
                    ? "bg-neon-red/10 text-neon-red border-neon-red/30 hover:bg-neon-red/20"
                    : "bg-neon-yellow/10 text-neon-yellow border-neon-yellow/30 hover:bg-neon-yellow/20"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {currentTab.isMonitoring ? "Stop Monitor" : "Start Monitor"}
              </button>
            </div>

            {/* Loading State */}
            {currentTab.isLoading && (
              <div className="flex items-center justify-center py-20">
                <Loader label="Scanning" />
              </div>
            )}

            {/* Error State */}
            {currentTab.error && (
              <div className="rounded-lg border border-neon-red/40 bg-neon-red/10 px-6 py-4 text-sm text-neon-red">
                {currentTab.error}
              </div>
            )}

            {/* Scan Results */}
            {currentTab.scanResult && !currentTab.isLoading && (
              <div className="grid gap-6 lg:grid-cols-3">
                <div className="rounded-lg border border-white/10 bg-gray-900/50 p-6">
                  <p className="text-sm font-semibold">Status</p>
                  <p className={`mt-4 text-3xl font-bold ${
                    currentTab.scanResult.status === "ONLINE" ? "text-neon-green" : "text-neon-red"
                  }`}>
                    {currentTab.scanResult.status}
                  </p>
                </div>

                <div className="rounded-lg border border-white/10 bg-gray-900/50 p-6">
                  <p className="text-sm font-semibold">Threat Score</p>
                  <p className={`mt-4 text-3xl font-bold ${getThreatColor(currentTab.scanResult.threatScore)}`}>
                    {currentTab.scanResult.threatScore}
                  </p>
                </div>

                <div className="rounded-lg border border-white/10 bg-gray-900/50 p-6">
                  <p className="text-sm font-semibold">Risk Level</p>
                  <span className={`mt-4 inline-flex rounded-lg border px-4 py-2 text-sm font-medium ${riskStyles[currentTab.scanResult.riskLevel]}`}>
                    {currentTab.scanResult.riskLevel}
                  </span>
                </div>

                <div className="lg:col-span-3 rounded-lg border border-white/10 bg-gray-900/50 p-6">
                  <p className="text-sm font-semibold">Content Preview</p>
                  <p className="mt-4 text-sm text-gray-300">{currentTab.scanResult.textPreview || "No preview available"}</p>
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Category</p>
                      <p className="mt-2 text-sm text-gray-200">{currentTab.scanResult.category}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Last Scanned</p>
                      <p className="mt-2 text-sm text-gray-200">{formatTimestamp(currentTab.scanResult.timestamp)}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
