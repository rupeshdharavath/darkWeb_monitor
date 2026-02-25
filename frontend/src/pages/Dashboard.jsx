import { useMemo, useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import StatusCard from "../components/StatusCard.jsx";
import ThreatScoreCard from "../components/ThreatScoreCard.jsx";
import CategoryPieChart from "../components/CategoryPieChart.jsx";
import ThreatBarChart from "../components/ThreatBarChart.jsx";
import TimelineChart from "../components/TimelineChart.jsx";
import Loader from "../components/Loader.jsx";
import {
  scanOnion,
  getHistoryEntry,
  createMonitor,
  deleteMonitor,
  getAlerts,
  compareScans
} from "../services/api.js";

const placeholderData = {
  status: "OFFLINE",
  threatScore: 0,
  category: "Unknown",
  riskLevel: "LOW",
  confidence: 0,
  threatIndicators: {},
  pgpDetected: false,
  emails: [],
  cryptoAddresses: [],
  contentChanged: false,
  contentHash: "",
  title: "Unknown",
  textPreview: "",
  keywords: [],
  links: [],
  fileLinks: [],
  fileAnalysis: [],
  clamav: {
    status: null,
    detected: false,
    details: []
  },
  responseTime: null,
  statusCode: null,
  timestamp: null,
  categoryDistribution: [],
  threatBreakdown: [],
  timeline: []
};

const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return "-";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(2)} MB`;
};

const formatMillis = (seconds) => {
  if (seconds === null || seconds === undefined) return "-";
  return `${(seconds * 1000).toFixed(0)} ms`;
};

const riskStyles = {
  LOW: "bg-neon-green/15 text-neon-green border-neon-green/40",
  MEDIUM: "bg-neon-yellow/15 text-neon-yellow border-neon-yellow/40",
  HIGH: "bg-neon-red/15 text-neon-red border-neon-red/40"
};

const MAX_TABS = 5;

const buildTab = (index, baseTimestamp) => ({
  id: baseTimestamp + index,
  url: "",
  scanResult: null,
  isLoading: false,
  error: "",
  monitorId: null,
  isMonitoring: false,
  comparison: null,
  compareError: ""
});

export default function Dashboard() {
  const { entryId } = useParams();
  const navigate = useNavigate();
  const [tabs, setTabs] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [alerts, setAlerts] = useState([]);
  const [showAlerts, setShowAlerts] = useState(false);

  // Load entry from history if entryId is provided
  useEffect(() => {
    if (entryId && tabs.length > 0) {
      loadHistoryEntry(entryId);
    }
  }, [entryId, tabs.length, activeTab]);

  // Initialize five tabs on first load
  useEffect(() => {
    if (tabs.length === 0) {
      const baseTimestamp = Date.now();
      const initialTabs = Array.from({ length: MAX_TABS }, (_, index) => buildTab(index, baseTimestamp));
      setTabs(initialTabs);
    }
  }, [tabs.length]);

  // Refresh alerts periodically (monitoring scans happen on backend)
  useEffect(() => {
    loadAlerts();
    const interval = setInterval(() => {
      loadAlerts();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadHistoryEntry = async (id) => {
    const updatedTabs = [...tabs];
    if (!updatedTabs[activeTab]) return;
    updatedTabs[activeTab].isLoading = true;
    updatedTabs[activeTab].error = "";
    setTabs(updatedTabs);
    try {
      const data = await getHistoryEntry(id);
      updatedTabs[activeTab].scanResult = { ...placeholderData, ...data };
      updatedTabs[activeTab].url = data.url || updatedTabs[activeTab].url;
      updatedTabs[activeTab].isLoading = false;
      setTabs(updatedTabs);
      if (data.url) {
        loadComparison(data.url, activeTab);
      }
    } catch (err) {
      updatedTabs[activeTab].error = "Failed to load scan entry. Please try again.";
      updatedTabs[activeTab].isLoading = false;
      setTabs(updatedTabs);
    }
  };

  const handleSearch = async (url, tabIndex) => {
    if (!url) return;
    const updatedTabs = [...tabs];
    updatedTabs[tabIndex].isLoading = true;
    updatedTabs[tabIndex].error = "";
    setTabs(updatedTabs);
    try {
      const data = await scanOnion(url);
      updatedTabs[tabIndex].scanResult = { ...placeholderData, ...data, url };
      updatedTabs[tabIndex].url = url;
      updatedTabs[tabIndex].isLoading = false;
      setTabs(updatedTabs);
      loadComparison(url, tabIndex);
    } catch (err) {
      updatedTabs[tabIndex].error = "Scan failed. Please check the URL or API availability.";
      updatedTabs[tabIndex].isLoading = false;
      setTabs(updatedTabs);
    }
  };

  const loadComparison = async (url, tabIndex) => {
    if (!url || !tabs[tabIndex]) return;
    try {
      const data = await compareScans(encodeURIComponent(url));
      const updatedTabs = [...tabs];
      updatedTabs[tabIndex].comparison = data;
      updatedTabs[tabIndex].compareError = "";
      setTabs(updatedTabs);
    } catch (err) {
      const updatedTabs = [...tabs];
      if (!updatedTabs[tabIndex]) return;
      updatedTabs[tabIndex].comparison = null;
      updatedTabs[tabIndex].compareError = "Not enough scans to compare yet.";
      setTabs(updatedTabs);
    }
  };

  const loadAlerts = async () => {
    try {
      const data = await getAlerts();
      const newAlerts = (data.alerts || []).filter((alert) => alert.status === "new");
      setAlerts(newAlerts);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    }
  };

  const toggleMonitoring = async (tabIndex) => {
    const tab = tabs[tabIndex];
    if (!tab) return;

    if (tab.isMonitoring) {
      try {
        await deleteMonitor(tab.monitorId);
        const updatedTabs = [...tabs];
        updatedTabs[tabIndex].isMonitoring = false;
        updatedTabs[tabIndex].monitorId = null;
        setTabs(updatedTabs);
      } catch (err) {
        console.error("Failed to stop monitoring:", err);
      }
      return;
    }

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
    } catch (err) {
      console.error("Failed to start monitoring:", err);
      alert("Failed to start monitoring");
    }
  };

  const currentTab = tabs[activeTab];
  const scanResult = currentTab?.scanResult || null;
  const isLoading = currentTab?.isLoading || false;
  const error = currentTab?.error || "";
  const comparison = currentTab?.comparison || null;
  const compareError = currentTab?.compareError || "";
  const displayData = scanResult || placeholderData;
  const displayUrl = scanResult?.url || currentTab?.url || "";

  const headerText = scanResult
    ? `Scan Results for ${displayUrl}`
    : "Darkweb Intelligence Console";

  const dataReady = !!scanResult;
  
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

  const badgeStyle = displayData.pgpDetected
    ? "bg-neon-green/15 text-neon-green border-neon-green/40"
    : "bg-white/5 text-gray-400 border-white/10";

  const contentChangeStyle = displayData.contentChanged
    ? "text-neon-yellow"
    : "text-gray-400";

  const riskStyle = riskStyles[displayData.riskLevel] || "bg-white/5 text-gray-400 border-white/10";
  const threatIndicators = displayData.threatIndicators || {};
  const keywordMatches = threatIndicators.matched_keywords || [];
  const fileAnalysis = displayData.fileAnalysis || [];
  const fileLinks = displayData.fileLinks || [];
  const links = displayData.links || [];
  const confidencePct = Math.round((displayData.confidence || 0) * 100);

  const sectionCards = useMemo(
    () => [
      { label: "Category", value: displayData.category },
      { label: "PGP Detected", value: displayData.pgpDetected ? "Yes" : "No" },
      { label: "Content Changed", value: displayData.contentChanged ? "Yes" : "No" }
    ],
    [displayData]
  );

  return (
    <div className="min-h-screen px-6 py-8 lg:px-16">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8">
        <header className="flex flex-col gap-4">
          {entryId && (
            <button
              onClick={() => navigate("/history")}
              className="flex w-fit items-center gap-2 rounded-lg bg-white/5 px-4 py-2 text-sm text-gray-400 transition-colors hover:bg-white/10 hover:text-gray-200"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to History
            </button>
          )}
          <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Cyber Threat Monitor</p>
          <h1 className="text-3xl font-semibold md:text-4xl">{headerText}</h1>
          <p className="text-sm text-gray-400">
            Real-time signals, behavioral markers, and intelligence indicators for onion services.
          </p>
          {scanResult && displayData.timestamp && (
            <p className="text-xs text-gray-500">
              Last scanned: {formatTimestamp(displayData.timestamp)}
            </p>
          )}
        </header>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Active Tabs</p>
            <p className="text-sm text-gray-400">Monitor up to {MAX_TABS} onion sites</p>
          </div>
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="relative rounded-lg bg-neon-red/10 px-4 py-2 text-sm font-medium text-neon-red border border-neon-red/30 hover:bg-neon-red/20 transition-colors"
          >
            Alerts {alerts.length > 0 && `(${alerts.length})`}
            {alerts.length > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-neon-red text-xs text-white">
                {alerts.length}
              </span>
            )}
          </button>
        </div>

        {showAlerts && (
          <div className="rounded-lg border border-neon-red/40 bg-neon-red/10 p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-neon-red">Threat Score Alerts</h3>
              <button
                onClick={() => setShowAlerts(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="mt-4 space-y-2 max-h-80 overflow-y-auto">
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

        <div className="flex items-center gap-2 border-b border-white/10 overflow-x-auto pb-2">
          {tabs.map((tab, index) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(index)}
              className={`flex flex-col items-start gap-1 rounded-t-lg border-x border-t px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === index
                  ? "border-neon-green/40 bg-gray-900 text-white"
                  : "border-white/10 bg-white/5 text-gray-400 hover:bg-white/10"
              }`}
            >
              <span className="flex items-center gap-2">
                {`Tab ${index + 1}`}
                {tab.isMonitoring && <span className="text-xs text-neon-green">●</span>}
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] ${
                    tab.scanResult?.status === "ONLINE"
                      ? "border-neon-green/40 text-neon-green"
                      : tab.scanResult?.status === "OFFLINE"
                        ? "border-neon-red/40 text-neon-red"
                        : "border-white/10 text-gray-400"
                  }`}
                >
                  {tab.scanResult?.status || "UNKNOWN"}
                </span>
              </span>
              <span className="text-[10px] text-gray-500">
                {tab.scanResult?.timestamp ? formatTimestamp(tab.scanResult.timestamp) : "Not scanned"}
              </span>
            </button>
          ))}
        </div>

        {currentTab && (
          <div className="flex flex-wrap items-center gap-4">
            <input
              type="text"
              placeholder="http://exampleonion.onion"
              value={currentTab.url || ""}
              onChange={(event) => {
                const updatedTabs = [...tabs];
                updatedTabs[activeTab].url = event.target.value;
                setTabs(updatedTabs);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch(currentTab.url, activeTab);
                }
              }}
              className="flex-1 min-w-[240px] rounded-xl border border-white/10 bg-gray-900/60 px-4 py-3 text-base text-gray-100 outline-none transition focus:border-neon-blue/70 focus:ring-2 focus:ring-neon-blue/30"
            />
            <button
              onClick={() => handleSearch(currentTab.url, activeTab)}
              disabled={isLoading || !currentTab.url}
              className="rounded-xl border border-neon-green/40 bg-neon-green/20 px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] text-neon-green transition hover:bg-neon-green/30 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? "Scanning" : "Search"}
            </button>
            <button
              onClick={() => toggleMonitoring(activeTab)}
              disabled={!currentTab.scanResult}
              className={`rounded-xl border px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] transition ${
                currentTab.isMonitoring
                  ? "border-neon-red/40 bg-neon-red/20 text-neon-red hover:bg-neon-red/30"
                  : "border-neon-yellow/40 bg-neon-yellow/20 text-neon-yellow hover:bg-neon-yellow/30"
              } disabled:cursor-not-allowed disabled:opacity-50`}
            >
              {currentTab.isMonitoring ? "Stop Monitor" : "Start Monitor"}
            </button>
          </div>
        )}

        {isLoading && (
          <div className="flex min-h-[50vh] items-center justify-center">
            <Loader label="Scanning" />
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-neon-red/40 bg-neon-red/10 px-6 py-4 text-sm text-neon-red">
            {error}
          </div>
        )}

        {dataReady && !isLoading && (
          <div className="flex flex-col gap-8">
            <div className="flex flex-col gap-6">
              <div className="grid gap-6 md:grid-cols-2">
                <StatusCard status={displayData.status} />
                <ThreatScoreCard score={displayData.threatScore} />
              </div>
            </div>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Current Scan</p>
                <div className="mt-4 space-y-3 text-sm text-gray-300">
                  <div className="flex items-center justify-between">
                    <span>Threat Score</span>
                    <span className="text-gray-200">{displayData.threatScore}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Risk Level</span>
                    <span className="text-gray-200">{displayData.riskLevel}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Status</span>
                    <span className="text-gray-200">{displayData.status}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Emails Found</span>
                    <span className="text-gray-200">{displayData.emails?.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Crypto Addresses</span>
                    <span className="text-gray-200">{displayData.cryptoAddresses?.length || 0}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Previous Scan</p>
                {comparison ? (
                  <div className="mt-4 space-y-3 text-sm text-gray-300">
                    <div className="flex items-center justify-between">
                      <span>Threat Score</span>
                      <span className="text-gray-200">{comparison.previous?.threat_score ?? "-"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Risk Level</span>
                      <span className="text-gray-200">{comparison.previous?.risk_level ?? "-"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Status</span>
                      <span className="text-gray-200">{comparison.previous?.url_status ?? "-"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Emails Found</span>
                      <span className="text-gray-200">{comparison.previous?.emails ?? 0}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Crypto Addresses</span>
                      <span className="text-gray-200">{comparison.previous?.crypto ?? 0}</span>
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-gray-500">{compareError || "Waiting for previous scan data."}</p>
                )}
              </div>
            </section>

            {comparison && (
              <section className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Changes Detected</p>
                <div className="mt-4 grid gap-4 text-sm text-gray-300 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="flex items-center justify-between">
                    <span>Threat Score Δ</span>
                    <span className={comparison.changes?.threat_score_delta > 0 ? "text-neon-red" : "text-gray-200"}>
                      {comparison.changes?.threat_score_delta ?? 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Risk Level Change</span>
                    <span className="text-gray-200">
                      {comparison.changes?.risk_level_changed ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Status Change</span>
                    <span className="text-gray-200">
                      {comparison.changes?.status_changed ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Category Change</span>
                    <span className="text-gray-200">
                      {comparison.changes?.category_changed ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>New Emails</span>
                    <span className="text-gray-200">{comparison.changes?.new_emails ?? 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>New Crypto</span>
                    <span className="text-gray-200">{comparison.changes?.new_crypto ?? 0}</span>
                  </div>
                </div>
              </section>
            )}

            <section className="grid gap-6 lg:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Risk Snapshot</p>
                <div className="mt-4 space-y-4 text-sm text-gray-300">
                  <div className="flex items-center justify-between">
                    <span>Risk Level</span>
                    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${riskStyle}`}>
                      {displayData.riskLevel}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Confidence</span>
                    <span className="text-gray-200">{confidencePct}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Response Time</span>
                    <span className="text-gray-200">{formatMillis(displayData.responseTime)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>HTTP Status</span>
                    <span className="text-gray-200">{displayData.statusCode ?? "-"}</span>
                  </div>
                  {displayData.timestamp && (
                    <div className="flex items-center justify-between">
                      <span>Scanned At</span>
                      <span className="text-xs text-gray-200">{formatTimestamp(displayData.timestamp)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6 lg:col-span-2">
                <p className="text-sm font-semibold">Threat Indicators</p>
                <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase tracking-[0.2em]">
                  <span className="rounded-full border border-white/10 px-3 py-1 text-gray-300">
                    Keyword Matches: {threatIndicators.keyword_matches ?? 0}
                  </span>
                  <span className={`rounded-full border px-3 py-1 ${threatIndicators.crypto_detected ? "border-neon-yellow/40 text-neon-yellow" : "border-white/10 text-gray-400"}`}>
                    Crypto {threatIndicators.crypto_detected ? "Detected" : "None"}
                  </span>
                  <span className={`rounded-full border px-3 py-1 ${threatIndicators.email_detected ? "border-neon-green/40 text-neon-green" : "border-white/10 text-gray-400"}`}>
                    Email {threatIndicators.email_detected ? "Detected" : "None"}
                  </span>
                  <span className={`rounded-full border px-3 py-1 ${threatIndicators.malware_detected ? "border-neon-red/40 text-neon-red" : "border-white/10 text-gray-400"}`}>
                    Malware {threatIndicators.malware_detected ? "Detected" : "None"}
                  </span>
                </div>
                <div className="mt-5 flex flex-wrap gap-2 text-sm text-gray-300">
                  {keywordMatches.length ? (
                    keywordMatches.map((keyword) => (
                      <span key={keyword} className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                        {keyword}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500">No matched keywords.</span>
                  )}
                </div>
              </div>
            </section>

            <section className="grid gap-6 md:grid-cols-3">
              {sectionCards.map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                  <p className="text-xs uppercase tracking-[0.3em] text-gray-400">{item.label}</p>
                  {item.label === "PGP Detected" ? (
                    <span className={`mt-4 inline-flex items-center rounded-full border px-3 py-1 text-sm ${badgeStyle}`}>
                      {item.value}
                    </span>
                  ) : (
                    <p className={`mt-4 text-2xl font-semibold ${item.label === "Content Changed" ? contentChangeStyle : ""}`}>
                      {item.value}
                    </p>
                  )}
                </div>
              ))}
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Emails</p>
                <ul className="mt-4 space-y-2 text-sm text-gray-300">
                  {displayData.emails?.length ? (
                    displayData.emails.map((email) => (
                      <li key={email} className="break-words text-xs sm:text-sm">
                        {email}
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-500">No emails detected.</li>
                  )}
                </ul>
              </div>
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Crypto Addresses</p>
                <ul className="mt-4 space-y-2 text-sm text-gray-300">
                  {displayData.cryptoAddresses?.length ? (
                    displayData.cryptoAddresses.map((address) => (
                      <li key={address} className="break-words text-xs sm:text-sm">
                        {address}
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-500">No addresses detected.</li>
                  )}
                </ul>
              </div>
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Signal Notes</p>
                <div className="mt-4 space-y-3 text-sm text-gray-300">
                  <div className="flex items-center justify-between">
                    <span>Content Changed</span>
                    <span className={contentChangeStyle}>{displayData.contentChanged ? "Yes" : "No"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>PGP Detected</span>
                    <span className={displayData.pgpDetected ? "text-neon-green" : "text-gray-400"}>
                      {displayData.pgpDetected ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Category</span>
                    <span className="text-gray-200">{displayData.category}</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6 lg:col-span-2">
                <p className="text-sm font-semibold">Content Preview</p>
                <p className="mt-3 text-sm text-gray-300">{displayData.textPreview || "No preview available."}</p>
                <div className="mt-5 grid gap-3 text-xs text-gray-400 sm:grid-cols-2">
                  <div>
                    <p className="uppercase tracking-[0.3em]">Title</p>
                    <p className="mt-2 text-sm text-gray-200">{displayData.title || "Unknown"}</p>
                  </div>
                  <div>
                    <p className="uppercase tracking-[0.3em]">Content Hash</p>
                    <p className="mt-2 break-words font-mono text-xs text-gray-200">
                      {displayData.contentHash || "-"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Keywords</p>
                <div className="mt-4 flex flex-wrap gap-2 text-sm text-gray-300">
                  {displayData.keywords?.length ? (
                    displayData.keywords.map((keyword) => (
                      <span key={keyword} className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                        {keyword}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500">No keywords extracted.</span>
                  )}
                </div>
              </div>
            </section>

            <section className="flex flex-col gap-6">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">Downloaded Files</p>
                  <span className="text-xs uppercase tracking-[0.3em] text-gray-500">
                    {fileAnalysis.length} files
                  </span>
                </div>
                <div className="mt-4 space-y-4">
                  {fileAnalysis.length ? (
                    fileAnalysis.map((file) => (
                      <div key={file.file_hash || file.file_url} className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-gray-300">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-semibold text-gray-100">{file.file_name || "Unnamed file"}</span>
                          <span className="text-xs text-gray-400">{formatBytes(file.file_size)}</span>
                        </div>
                        <div className="mt-2 grid gap-2 text-xs text-gray-400 sm:grid-cols-2">
                          <div>
                            <span className="uppercase tracking-[0.2em]">Type</span>
                            <p className="mt-1 text-sm text-gray-200">{file.content_type || "Unknown"}</p>
                          </div>
                          <div>
                            <span className="uppercase tracking-[0.2em]">Hash</span>
                            <p className="mt-1 break-words font-mono text-xs text-gray-200">{file.file_hash || "-"}</p>
                          </div>
                        </div>
                        {file.analysis && (
                          <div className="mt-4 space-y-3">
                            <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                              <p className="text-xs uppercase tracking-[0.2em] text-gray-400">ClamAV Scan</p>
                              <div className="mt-2 space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Status</span>
                                  <span className={file.analysis.clamav_detected ? "text-neon-red" : "text-neon-green"}>
                                    {file.analysis.clamav_status || "Not available"}
                                  </span>
                                </div>
                                {file.analysis.clamav_detected && file.analysis.clamav?.threats?.length > 0 && (
                                  <div className="mt-2 space-y-1">
                                    {file.analysis.clamav.threats.map((threat, idx) => (
                                      <p key={idx} className="text-xs text-neon-red">
                                        ⚠️ {threat.threat_name || "Threat detected"}
                                      </p>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>

                            {file.analysis.strings && (
                              <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                                <p className="text-xs uppercase tracking-[0.2em] text-gray-400">Strings Analysis</p>
                                <div className="mt-2 text-sm text-gray-300">
                                  <p className="text-xs text-gray-400">
                                    {file.analysis.strings.strings_found || 0} readable strings found
                                  </p>
                                  {file.analysis.strings.sample_strings?.length > 0 && (
                                    <div className="mt-2 max-h-32 space-y-1 overflow-y-auto text-xs text-gray-500">
                                      {file.analysis.strings.sample_strings.slice(0, 5).map((str, idx) => (
                                        <p key={idx} className="break-words font-mono">{str}</p>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {file.analysis.exiftool?.success && (
                              <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                                <p className="text-xs uppercase tracking-[0.2em] text-gray-400">Metadata (Exiftool)</p>
                                <div className="mt-2 space-y-1 text-xs text-gray-300">
                                  <p className="text-gray-400">{file.analysis.exiftool.field_count || 0} fields extracted</p>
                                  {file.analysis.exiftool.metadata && (
                                    <div className="mt-2 max-h-32 space-y-1 overflow-y-auto">
                                      {Object.entries(file.analysis.exiftool.metadata).slice(0, 8).map(([key, value]) => (
                                        <div key={key} className="flex justify-between gap-2">
                                          <span className="text-gray-500">{key}:</span>
                                          <span className="break-words text-right text-gray-200">{String(value)}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {file.analysis.binwalk?.success && file.analysis.binwalk.signatures?.length > 0 && (
                              <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                                <p className="text-xs uppercase tracking-[0.2em] text-gray-400">Binwalk Signatures</p>
                                <div className="mt-2 max-h-32 space-y-1 overflow-y-auto text-xs text-gray-300">
                                  {file.analysis.binwalk.signatures.map((sig, idx) => (
                                    <p key={idx} className="break-words text-gray-400">{sig}</p>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        <p className="mt-3 break-words text-xs text-gray-500">{file.file_url}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No files downloaded yet.</p>
                  )}
                </div>

                <div className="mt-6">
                  <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Detected File Links</p>
                  <ul className="mt-3 space-y-2 text-sm text-gray-300">
                    {fileLinks.length ? (
                      fileLinks.map((fileLink) => (
                        <li key={fileLink.url || fileLink.text} className="break-words">
                          <span className="text-gray-500">{fileLink.extension || "file"}: </span>
                          <span className="text-gray-200">{fileLink.url}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-gray-500">No file links detected.</li>
                    )}
                  </ul>
                </div>
              </div>

              <section className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold">ClamAV Malware Scan</p>
                    <p className="mt-1 text-xs text-gray-400">Signature scan results from downloaded files.</p>
                  </div>
                  <span
                    className={`rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${displayData.clamav?.detected ? "border-neon-red/40 text-neon-red" : "border-neon-green/40 text-neon-green"}`}
                  >
                    {displayData.clamav?.detected ? "Threats Found" : "No Threats"}
                  </span>
                </div>
                <div className="mt-4 grid gap-4 text-sm text-gray-300 sm:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Status</p>
                    <p className="mt-2 text-gray-200">{displayData.clamav?.status || "Not available"}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Detections</p>
                    <p className="mt-2 text-gray-200">{displayData.clamav?.details?.length || 0}</p>
                  </div>
                </div>
                <div className="mt-4 space-y-2 text-sm text-gray-300">
                  {displayData.clamav?.details?.length ? (
                    displayData.clamav.details.map((detail) => (
                      <div key={detail.file} className="rounded-lg border border-white/10 bg-white/5 p-3">
                        <p className="break-words text-sm text-gray-100">{detail.file}</p>
                        <p className="mt-1 text-xs text-gray-400">
                          {(detail.threats || []).join(", ") || "Threat detected"}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No ClamAV detections reported.</p>
                  )}
                </div>
              </section>

              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Links Observed</p>
                <p className="mt-2 text-xs text-gray-400">Showing up to {links.length} links</p>
                <ul className="mt-4 space-y-2 text-sm text-gray-300">
                  {links.length ? (
                    links.map((link) => (
                      <li key={link.url} className="break-words">
                        <span className="text-gray-500">{link.text || "Link"}: </span>
                        <span className="text-gray-200">{link.url}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-500">No links captured.</li>
                  )}
                </ul>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <CategoryPieChart data={displayData.categoryDistribution} />
              <ThreatBarChart data={displayData.threatBreakdown} />
              <TimelineChart data={displayData.timeline} />
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
