import { useMemo, useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams, useLocation } from "react-router-dom";
import StatusCard from "../components/StatusCard.jsx";
import ThreatScoreCard from "../components/ThreatScoreCard.jsx";
import CategoryPieChart from "../components/CategoryPieChart.jsx";
import ThreatBarChart from "../components/ThreatBarChart.jsx";
import TimelineChart from "../components/TimelineChart.jsx";
import Loader from "../components/Loader.jsx";
import ScanProgress from "../components/ScanProgress.jsx";
import { useToast } from "../hooks/useToast.jsx";
import {
  scanOnion,
  getHistoryEntry,
  createMonitor,
  deleteMonitor,
  getMonitor,
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

export default function Dashboard() {
  const { entryId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const queryUrl = searchParams.get("url");
  const { alertData = null } = location.state || {};
  const { showToast, ToastContainer } = useToast();
  const [url, setUrl] = useState("");
  const [scanResult, setScanResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [monitorId, setMonitorId] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [compareError, setCompareError] = useState("");
  const [alerts, setAlerts] = useState([]);
  const [showAlerts, setShowAlerts] = useState(false);
  const [isTogglingMonitor, setIsTogglingMonitor] = useState(false);

  // Load persisted state from localStorage on mount
  useEffect(() => {
    if (!entryId && !queryUrl) {
      try {
        const savedState = localStorage.getItem('dashboardState');
        if (savedState) {
          const { url: savedUrl, scanResult: savedResult, monitorId: savedMonitorId } = JSON.parse(savedState);
          if (savedUrl) setUrl(savedUrl);
          if (savedResult) {
            setScanResult(savedResult);
            loadComparison(savedUrl);
          }
          if (savedMonitorId) {
            setMonitorId(savedMonitorId);
            verifyMonitor(savedMonitorId);
          }
        }
      } catch (err) {
        console.error('Failed to load saved dashboard state:', err);
      }
    }
  }, []);

  // Load URL from query parameter on mount
  useEffect(() => {
    if (queryUrl) {
      try {
        // Decode the URL from query param
        const decodedUrl = decodeURIComponent(queryUrl);
        setUrl(decodedUrl);
        handleSearchWithUrl(decodedUrl);
      } catch (err) {
        console.error("Failed to decode URL from query param:", err);
      }
    }
  }, [queryUrl]);

  const handleSearchWithUrl = async (urlToSearch) => {
    if (!urlToSearch.trim()) return;
    
    setIsLoading(true);
    setError("");
    try {
      const data = await scanOnion(urlToSearch.trim());
      const newScanResult = { ...placeholderData, ...data, url: urlToSearch.trim() };
      setScanResult(newScanResult);
      setUrl(urlToSearch.trim());
      loadComparison(urlToSearch.trim());
      // Save to localStorage
      localStorage.setItem('dashboardState', JSON.stringify({
        url: urlToSearch.trim(),
        scanResult: newScanResult,
        monitorId
      }));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Scan failed");
      setScanResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Verify if monitor still exists
  const verifyMonitor = async (monitorIdToCheck) => {
    try {
      await getMonitor(monitorIdToCheck);
      setIsMonitoring(true);
    } catch (err) {
      // Monitor doesn't exist anymore
      setIsMonitoring(false);
      setMonitorId(null);
    }
  };

  // Load entry from history if entryId is provided
  useEffect(() => {
    if (entryId) {
      loadHistoryEntry(entryId);
    }
  }, [entryId]);

  // Refresh alerts periodically
  useEffect(() => {
    loadAlerts();
    const interval = setInterval(() => {
      loadAlerts();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Periodically verify monitor status
  useEffect(() => {
    if (monitorId) {
      const interval = setInterval(() => {
        verifyMonitor(monitorId);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [monitorId]);

  const loadHistoryEntry = async (id) => {
    setIsLoading(true);
    setError("");
    try {
      const data = await getHistoryEntry(id);
      const loadedResult = { ...placeholderData, ...data };
      setScanResult(loadedResult);
      setUrl(data.url || "");
      setIsLoading(false);
      if (data.url) {
        loadComparison(data.url);
      }
      // Save to localStorage
      localStorage.setItem('dashboardState', JSON.stringify({
        url: data.url,
        scanResult: loadedResult,
        monitorId
      }));
    } catch (err) {
      setError("Failed to load scan entry. Please try again.");
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!url) return;
    setIsLoading(true);
    setError("");
    try {
      const data = await scanOnion(url);
      const newScanResult = { ...placeholderData, ...data, url };
      setScanResult(newScanResult);
      setIsLoading(false);
      loadComparison(url);
      // Save to localStorage
      localStorage.setItem('dashboardState', JSON.stringify({
        url,
        scanResult: newScanResult,
        monitorId
      }));
    } catch (err) {
      setError("Scan failed. Please check the URL or API availability.");
      setIsLoading(false);
    }
  };

  const loadComparison = async (urlToCompare) => {
    if (!urlToCompare) return;
    try {
      const data = await compareScans(urlToCompare);
      setComparison(data);
      setCompareError("");
    } catch (err) {
      setComparison(null);
      setCompareError("Not enough scans to compare yet.");
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

  const toggleMonitoring = async () => {
    if (isMonitoring) {
      setIsTogglingMonitor(true);
      try {
        await deleteMonitor(monitorId);
        setIsMonitoring(false);
        setMonitorId(null);
        // Update localStorage
        localStorage.setItem('dashboardState', JSON.stringify({
          url,
          scanResult,
          monitorId: null
        }));
        showToast("Monitor stopped successfully", "success");
      } catch (err) {
        console.error("Failed to stop monitoring:", err);
        showToast("Failed to stop monitoring: " + (err.response?.data?.detail || err.message), "error");
      } finally {
        setIsTogglingMonitor(false);
      }
      return;
    }

    if (!url) {
      showToast("Please scan a URL first", "warning");
      return;
    }

    setIsTogglingMonitor(true);
    try {
      const data = await createMonitor(url, 5);
      setIsMonitoring(true);
      setMonitorId(data.monitor_id);
      // Update localStorage
      localStorage.setItem('dashboardState', JSON.stringify({
        url,
        scanResult,
        monitorId: data.monitor_id
      }));
      showToast("Monitor created successfully! Visit the Monitors page to view and manage all monitors.", "success", 5000);
    } catch (err) {
      console.error("Failed to start monitoring:", err);
      const errorMessage = err.response?.data?.detail || err.message || "Unknown error occurred";
      showToast("Failed to start monitoring: " + errorMessage, "error");
    } finally {
      setIsTogglingMonitor(false);
    }
  };

  const displayData = scanResult || placeholderData;
  const displayUrl = scanResult?.url || url || "";

  const headerText = scanResult
    ? "Scan Results"
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
          {scanResult && displayUrl && (
            <p className="break-all text-sm text-neon-blue font-mono bg-gray-900/50 p-3 rounded-lg border border-white/10">
              {displayUrl}
            </p>
          )}
          <p className="text-sm text-gray-400">
            Real-time signals, behavioral markers, and intelligence indicators for onion services.
          </p>
          {scanResult && displayData.timestamp && (
            <p className="text-xs text-gray-500">
              Last scanned: {formatTimestamp(displayData.timestamp)}
            </p>
          )}
        </header>

        {/* Alert Context - Show what changed */}
        {alertData && (
          <div className="rounded-xl border border-neon-yellow/40 bg-neon-yellow/10 p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <p className="text-sm font-semibold text-neon-yellow">Alert Context</p>
                <p className="text-xs text-gray-400 mt-1">Details of what triggered this alert</p>
              </div>
              <button
                onClick={() => window.history.back()}
                className="text-xs text-gray-400 hover:text-gray-300"
              >
                ✕
              </button>
            </div>
            <div className="grid gap-4 text-sm sm:grid-cols-2">
              {alertData.reason && (
                <div>
                  <span className="text-xs uppercase tracking-wider text-gray-500">Alert Reason</span>
                  <p className="mt-1 text-gray-300 font-medium">{alertData.reason}</p>
                </div>
              )}
              {alertData.threat_score !== undefined && alertData.previous_score !== undefined && (
                <>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500">Previous Threat Score</span>
                    <p className="mt-1 text-lg font-semibold text-gray-300">{alertData.previous_score}</p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500">Current Threat Score</span>
                    <p className="mt-1 text-lg font-semibold text-neon-red">{alertData.threat_score}</p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500">Increase</span>
                    <p className="mt-1 text-lg font-semibold text-neon-yellow">+{alertData.score_increase}</p>
                  </div>
                </>
              )}
              {alertData.severity && (
                <div>
                  <span className="text-xs uppercase tracking-wider text-gray-500">Severity</span>
                  <p className="mt-1 text-gray-300">{alertData.severity}</p>
                </div>
              )}
              {alertData.details && (
                <div className="sm:col-span-2">
                  <span className="text-xs uppercase tracking-wider text-gray-500">Details</span>
                  <div className="mt-2 space-y-1 text-xs text-gray-300">
                    {alertData.details.content_changed && <p>• Content has changed</p>}
                    {alertData.details.malware_detected && <p>• Malware detected</p>}
                    {alertData.details.new_emails > 0 && <p>• {alertData.details.new_emails} new email(s) found</p>}
                    {alertData.details.new_crypto > 0 && <p>• {alertData.details.new_crypto} new crypto address(es) found</p>}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500">URL Scanner</p>
            <p className="text-sm text-gray-400">Instant threat analysis for dark web sites</p>
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
                      <button
                        onClick={() => {
                          setShowAlerts(false);
                          navigate("/?url=" + encodeURIComponent(alert.url), { 
                            state: { alertData: alert } 
                          });
                        }}
                        className="flex-shrink-0 rounded-lg border border-neon-blue/40 bg-neon-blue/10 px-3 py-2 text-xs font-medium text-neon-blue hover:bg-neon-blue/20 transition-colors"
                      >
                        View
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* URL Input and Actions */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[240px]">
            <input
              type="text"
              placeholder="http://exampleonion.onion"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && url) {
                  handleSearch();
                }
              }}
              className="w-full rounded-xl border border-white/10 bg-gray-900/60 px-4 py-3 text-base text-gray-100 outline-none transition focus:border-neon-blue/70 focus:ring-2 focus:ring-neon-blue/30 font-mono"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isLoading || !url}
            className="rounded-xl border border-neon-green/40 bg-neon-green/20 px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] text-neon-green transition hover:bg-neon-green/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "Scanning" : "Search"}
          </button>
          <button
            onClick={toggleMonitoring}
            disabled={!scanResult || isTogglingMonitor}
            className={`rounded-xl border px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] transition flex items-center gap-2 ${
              isMonitoring
                ? "border-neon-red/40 bg-neon-red/20 text-neon-red hover:bg-neon-red/30"
                : "border-neon-yellow/40 bg-neon-yellow/20 text-neon-yellow hover:bg-neon-yellow/30"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {isTogglingMonitor && (
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            <span>{isTogglingMonitor ? (isMonitoring ? "Stopping..." : "Starting...") : (isMonitoring ? "Stop Monitor" : "Start Monitor")}</span>
          </button>
        </div>

        {isLoading && (
          <div className="flex min-h-[50vh] items-center justify-center">
            <ScanProgress />
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
                <p className="text-sm font-semibold">Baseline Scan</p>
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
                  <p className="mt-4 text-sm text-gray-500">Perform another scan to compare with this baseline.</p>
                )}
              </div>
            </section>

            {comparison && (
              <section className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold mb-4">Changes Since Baseline</p>
                
                <div className="mb-4 flex items-center justify-between rounded-lg border border-neon-yellow/30 bg-neon-yellow/10 p-3">
                  <span className="text-sm text-neon-yellow">Threat Score Change</span>
                  <span className={`text-lg font-semibold ${
                    comparison.changes?.threat_score_delta > 0 
                      ? "text-neon-red" 
                      : comparison.changes?.threat_score_delta < 0 
                      ? "text-neon-green" 
                      : "text-gray-300"
                  }`}>
                    {comparison.changes?.threat_score_delta > 0 ? "+" : ""}{comparison.changes?.threat_score_delta ?? 0}
                  </span>
                </div>

                {comparison.reasons && comparison.reasons.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Reasons for Change</p>
                    {comparison.reasons.map((reason, idx) => (
                      <div key={idx} className="flex items-start gap-3 rounded-lg border border-white/5 bg-gray-800/30 p-3">
                        <span className="text-lg flex-shrink-0">{reason.charAt(0)}</span>
                        <p className="text-sm text-gray-300">{reason.substring(2)}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No significant changes detected.</p>
                )}

                <div className="mt-6 grid gap-3 text-sm text-gray-300 sm:grid-cols-2">
                  <div className="flex items-center justify-between rounded-lg border border-white/5 bg-gray-800/30 p-3">
                    <span>New Emails</span>
                    <span className={comparison.changes?.new_emails > 0 ? "text-neon-red font-semibold" : "text-gray-200"}>
                      {comparison.changes?.new_emails > 0 ? "+" : ""}{comparison.changes?.new_emails ?? 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-white/5 bg-gray-800/30 p-3">
                    <span>New Crypto Addresses</span>
                    <span className={comparison.changes?.new_crypto > 0 ? "text-neon-red font-semibold" : "text-gray-200"}>
                      {comparison.changes?.new_crypto > 0 ? "+" : ""}{comparison.changes?.new_crypto ?? 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-white/5 bg-gray-800/30 p-3">
                    <span>Risk Level Changed</span>
                    <span className="text-gray-200">
                      {comparison.changes?.risk_level_changed ? "✓ Yes" : "✗ No"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-white/5 bg-gray-800/30 p-3">
                    <span>Status Changed</span>
                    <span className="text-gray-200">
                      {comparison.changes?.status_changed ? "✓ Yes" : "✗ No"}
                    </span>
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
                      fileLinks.map((fileLink, idx) => (
                        <li key={`file-link-${idx}`} className="break-words">
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
                    links.map((link, idx) => (
                      <li key={`link-${idx}`} className="break-words">
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
      <ToastContainer />
    </div>
  );
}
