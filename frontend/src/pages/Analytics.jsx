import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getHistory } from "../services/api.js";
import Loader from "../components/Loader.jsx";
import CategoryPieChart from "../components/CategoryPieChart.jsx";

export default function Analytics() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showCategoryModal, setShowCategoryModal] = useState(false);

  useEffect(() => {
    loadHistory(true); // Initial load with loading state
  }, []);

  const loadHistory = async (showLoading = true) => {
    if (showLoading) {
      setIsLoading(true);
    }
    setError("");
    try {
      const data = await getHistory();
      setHistory(data.history || []);
    } catch (err) {
      setError("Failed to load analytics data.");
      console.error(err);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  };

  // Calculate statistics
  const totalScans = history.length;
  const uniqueUrls = new Set(history.map(h => h.url)).size;
  const avgThreatScore = history.length > 0
    ? Math.round(history.reduce((sum, h) => sum + (h.threat_score || 0), 0) / history.length)
    : 0;

  const highRiskCount = history.filter(h => h.risk_level === "HIGH").length;
  const mediumRiskCount = history.filter(h => h.risk_level === "MEDIUM").length;
  const lowRiskCount = history.filter(h => h.risk_level === "LOW").length;

  const onlineCount = history.filter(h => h.url_status === "ONLINE").length;
  const offlineCount = history.filter(h => h.url_status === "OFFLINE").length;

  // Category distribution
  const categoryMap = {};
  history.forEach(h => {
    const cat = h.category || "Unknown";
    categoryMap[cat] = (categoryMap[cat] || 0) + 1;
  });
  const categoryData = Object.entries(categoryMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  // Risk distribution for pie chart
  const riskData = [
    { name: "HIGH", value: highRiskCount },
    { name: "MEDIUM", value: mediumRiskCount },
    { name: "LOW", value: lowRiskCount }
  ].filter(d => d.value > 0);

  // Timeline data (last 30 days)
  const last30Days = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];
    last30Days.push({
      date: dateStr,
      count: 0
    });
  }

  history.forEach(h => {
    if (h.timestamp) {
      const dateStr = h.timestamp.split('T')[0];
      const entry = last30Days.find(d => d.date === dateStr);
      if (entry) entry.count++;
    }
  });

  // Top threat scores
  const topThreats = [...history]
    .sort((a, b) => (b.threat_score || 0) - (a.threat_score || 0))
    .slice(0, 10);

  // Get URLs for selected category
  const categoryUrls = selectedCategory
    ? history.filter(h => (h.category || "Unknown") === selectedCategory)
    : [];

  const handleCategoryClick = (categoryName) => {
    setSelectedCategory(categoryName);
    setShowCategoryModal(true);
  };

  const handleThreatClick = (url) => {
    navigate(`/?url=${encodeURIComponent(url)}`);
  };

  const handleUrlClick = (url) => {
    setShowCategoryModal(false);
    navigate(`/?url=${encodeURIComponent(url)}`);
  };

  return (
    <div className="min-h-screen px-6 py-12 lg:px-16">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-10">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Intelligence Analytics</p>
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold md:text-4xl">Platform Statistics</h1>
            <button
              onClick={() => loadHistory(false)}
              className="rounded-lg border border-neon-green/40 bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green hover:bg-neon-green/20 transition-colors"
            >
              Refresh
            </button>
          </div>
          <p className="text-sm text-gray-400">
            Comprehensive overview of all scanning activities and threat intelligence.
          </p>
        </header>

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

        {!isLoading && !error && (
          <>
            {/* Overview Stats */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Total Scans</p>
                <p className="mt-3 text-3xl font-semibold text-gray-100">{totalScans}</p>
                <p className="mt-2 text-xs text-gray-500">All time</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Unique Sites</p>
                <p className="mt-3 text-3xl font-semibold text-neon-blue">{uniqueUrls}</p>
                <p className="mt-2 text-xs text-gray-500">Tracked</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Avg Threat Score</p>
                <p className="mt-3 text-3xl font-semibold text-neon-yellow">{avgThreatScore}</p>
                <p className="mt-2 text-xs text-gray-500">Out of 100</p>
              </div>
              <div className="rounded-xl border border-neon-red/40 bg-neon-red/5 p-6">
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">High Risk Sites</p>
                <p className="mt-3 text-3xl font-semibold text-neon-red">{highRiskCount}</p>
                <p className="mt-2 text-xs text-gray-500">Critical attention needed</p>
              </div>
            </div>

            {/* Risk & Status Distribution */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <h2 className="text-lg font-semibold mb-4">Risk Distribution</h2>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2 text-sm">
                      <span className="text-neon-red">High Risk</span>
                      <span className="text-gray-300">{highRiskCount} ({totalScans > 0 ? Math.round((highRiskCount / totalScans) * 100) : 0}%)</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-white/5">
                      <div
                        className="h-3 rounded-full bg-neon-red"
                        style={{ width: `${totalScans > 0 ? (highRiskCount / totalScans) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2 text-sm">
                      <span className="text-neon-yellow">Medium Risk</span>
                      <span className="text-gray-300">{mediumRiskCount} ({totalScans > 0 ? Math.round((mediumRiskCount / totalScans) * 100) : 0}%)</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-white/5">
                      <div
                        className="h-3 rounded-full bg-neon-yellow"
                        style={{ width: `${totalScans > 0 ? (mediumRiskCount / totalScans) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2 text-sm">
                      <span className="text-neon-green">Low Risk</span>
                      <span className="text-gray-300">{lowRiskCount} ({totalScans > 0 ? Math.round((lowRiskCount / totalScans) * 100) : 0}%)</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-white/5">
                      <div
                        className="h-3 rounded-full bg-neon-green"
                        style={{ width: `${totalScans > 0 ? (lowRiskCount / totalScans) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <h2 className="text-lg font-semibold mb-4">Site Status</h2>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2 text-sm">
                      <span className="text-neon-green">Online</span>
                      <span className="text-gray-300">{onlineCount} ({totalScans > 0 ? Math.round((onlineCount / totalScans) * 100) : 0}%)</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-white/5">
                      <div
                        className="h-3 rounded-full bg-neon-green"
                        style={{ width: `${totalScans > 0 ? (onlineCount / totalScans) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2 text-sm">
                      <span className="text-neon-red">Offline</span>
                      <span className="text-gray-300">{offlineCount} ({totalScans > 0 ? Math.round((offlineCount / totalScans) * 100) : 0}%)</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-white/5">
                      <div
                        className="h-3 rounded-full bg-neon-red"
                        style={{ width: `${totalScans > 0 ? (offlineCount / totalScans) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Category Distribution */}
            <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4">Category Distribution (Click to view URLs)</h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {categoryData.map((cat) => (
                  <button
                    key={cat.name}
                    onClick={() => handleCategoryClick(cat.name)}
                    className="rounded-lg border border-white/10 bg-white/5 p-4 hover:border-neon-green/50 hover:bg-neon-green/10 transition-all duration-200 cursor-pointer text-left group"
                  >
                    <p className="text-sm font-medium text-gray-300 group-hover:text-neon-green transition-colors">{cat.name}</p>
                    <p className="mt-2 text-2xl font-semibold text-neon-green">{cat.value}</p>
                    <p className="mt-1 text-xs text-gray-500">
                      {totalScans > 0 ? Math.round((cat.value / totalScans) * 100) : 0}% of total
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Scanning Activity (Last 30 Days) */}
            <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4">Scanning Activity (Last 30 Days)</h2>
              <div className="flex items-end gap-1 h-48">
                {last30Days.map((day, index) => {
                  const maxCount = Math.max(...last30Days.map(d => d.count), 1);
                  const heightPercent = (day.count / maxCount) * 100;
                  return (
                    <div key={index} className="flex-1 flex flex-col justify-end group relative">
                      <div
                        className="bg-neon-green/70 hover:bg-neon-green transition-colors rounded-t"
                        style={{ height: `${heightPercent}%`, minHeight: day.count > 0 ? "4px" : "0" }}
                      ></div>
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-800 text-xs text-white px-2 py-1 rounded whitespace-nowrap">
                        {day.date}<br/>{day.count} scans
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-3 flex justify-between text-xs text-gray-500">
                <span>30 days ago</span>
                <span>Today</span>
              </div>
            </div>

            {/* Top Threats */}
            <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4">Top 10 Highest Threat Scores (Click to view dashboard)</h2>
              <div className="space-y-3">
                {topThreats.slice(0, 10).map((threat, index) => (
                  <button
                    key={threat.id || index}
                    onClick={() => handleThreatClick(threat.url)}
                    className="w-full flex items-center justify-between gap-4 rounded-lg border border-white/10 bg-white/5 p-4 hover:border-neon-red/50 hover:bg-neon-red/10 transition-all duration-200 cursor-pointer group"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-sm font-medium text-gray-400 group-hover:bg-neon-red/20 transition-colors">
                        {index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="break-words text-sm font-medium text-gray-200 group-hover:text-neon-red transition-colors">
                          {threat.url}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {threat.category} • {threat.risk_level}
                        </p>
                      </div>
                    </div>
                    <span className="rounded-full border border-neon-red/40 bg-neon-red/10 px-4 py-2 text-lg font-bold text-neon-red">
                      {threat.threat_score || 0}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Category URLs Modal */}
        {showCategoryModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-xl border border-white/10 bg-gray-900 shadow-2xl flex flex-col">
              {/* Modal Header */}
              <div className="border-b border-white/10 bg-gray-800/50 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-white">URLs in Category</h3>
                    <p className="mt-1 text-sm text-gray-400">{selectedCategory}</p>
                  </div>
                  <button
                    onClick={() => setShowCategoryModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="overflow-y-auto flex-1 p-6">
                <div className="space-y-2">
                  {categoryUrls.length > 0 ? (
                    categoryUrls.map((item, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleUrlClick(item.url)}
                        className="w-full text-left flex items-start gap-4 rounded-lg border border-white/10 bg-white/5 p-4 hover:border-neon-green/50 hover:bg-neon-green/10 transition-all duration-200 group"
                      >
                        <div className="mt-1">
                          <div className="h-4 w-4 rounded border border-gray-500 flex items-center justify-center group-hover:border-neon-green group-hover:bg-neon-green/20">
                            <span className="text-xs text-gray-400 group-hover:text-neon-green">→</span>
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="break-all text-sm font-medium text-gray-200 group-hover:text-neon-green transition-colors">
                            {item.url}
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            Threat: {item.threat_score || 0} • Risk: {item.risk_level} • Status: {item.url_status}
                          </p>
                        </div>
                      </button>
                    ))
                  ) : (
                    <p className="text-center text-gray-500 py-8">No URLs found in this category</p>
                  )}
                </div>
              </div>

              {/* Modal Footer */}
              <div className="border-t border-white/10 bg-gray-800/30 px-6 py-4">
                <p className="text-xs text-gray-500 text-center">
                  Click any URL to view its dashboard analysis
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
