import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../services/api.js";
import Loader from "../components/Loader.jsx";

const riskStyles = {
  LOW: "bg-neon-green/15 text-neon-green border-neon-green/40",
  MEDIUM: "bg-neon-yellow/15 text-neon-yellow border-neon-yellow/40",
  HIGH: "bg-neon-red/15 text-neon-red border-neon-red/40"
};

const statusStyles = {
  ONLINE: "bg-neon-green/15 text-neon-green",
  OFFLINE: "bg-neon-red/15 text-neon-red",
  UNKNOWN: "bg-gray-500/15 text-gray-400"
};

export default function History() {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await getHistory();
      setHistory(data.history || []);
    } catch (err) {
      setError("Failed to load history. Please try again.");
      console.error(err);
    } finally {
      setIsLoading(false);
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

  const getThreatScoreColor = (score) => {
    if (score >= 70) return "text-neon-red";
    if (score >= 40) return "text-neon-yellow";
    return "text-neon-green";
  };

  return (
    <div className="min-h-screen px-6 py-12 lg:px-16">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Scan History</p>
          <h1 className="text-3xl font-semibold md:text-4xl">Previous Scans</h1>
          <p className="text-sm text-gray-400">
            View and access your previously scanned onion sites and their threat analysis.
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

        {!isLoading && !error && history.length === 0 && (
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
            <svg className="h-16 w-16 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-500">No scan history available yet.</p>
            <Link
              to="/"
              className="mt-2 rounded-lg bg-neon-green/10 px-4 py-2 text-sm font-medium text-neon-green border border-neon-green/30 hover:bg-neon-green/20 transition-colors"
            >
              Start Scanning
            </Link>
          </div>
        )}

        {!isLoading && !error && history.length > 0 && (
          <div className="space-y-4">
            {history.map((entry) => (
              <Link
                key={entry.id}
                to={`/entry/${entry.id}`}
                className="block rounded-lg border border-white/10 bg-white/5 p-6 transition-all hover:border-neon-green/40 hover:bg-white/10"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-medium text-white line-clamp-1">
                        {entry.title}
                      </h3>
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${statusStyles[entry.url_status] || statusStyles.UNKNOWN}`}>
                        {entry.url_status}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-400 font-mono line-clamp-1">
                      {entry.url}
                    </p>

                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{formatTimestamp(entry.timestamp)}</span>
                      <span>•</span>
                      <span>{entry.category}</span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Threat Score:</span>
                      <span className={`text-2xl font-bold ${getThreatScoreColor(entry.threat_score)}`}>
                        {entry.threat_score}
                      </span>
                    </div>
                    
                    <span className={`inline-flex rounded-lg border px-3 py-1 text-xs font-medium ${riskStyles[entry.risk_level] || riskStyles.LOW}`}>
                      {entry.risk_level} RISK
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
