import { useMemo, useState } from "react";
import SearchBar from "../components/SearchBar.jsx";
import StatusCard from "../components/StatusCard.jsx";
import ThreatScoreCard from "../components/ThreatScoreCard.jsx";
import CategoryPieChart from "../components/CategoryPieChart.jsx";
import ThreatBarChart from "../components/ThreatBarChart.jsx";
import TimelineChart from "../components/TimelineChart.jsx";
import Loader from "../components/Loader.jsx";
import { scanOnion } from "../services/api.js";

const placeholderData = {
  status: "OFFLINE",
  threatScore: 0,
  category: "Unknown",
  pgpDetected: false,
  emails: [],
  cryptoAddresses: [],
  contentChanged: false,
  categoryDistribution: [],
  threatBreakdown: [],
  timeline: []
};

export default function Dashboard() {
  const [scanResult, setScanResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (url) => {
    setIsLoading(true);
    setError("");
    try {
      const data = await scanOnion(url);
      setScanResult({ ...placeholderData, ...data, url });
    } catch (err) {
      setError("Scan failed. Please check the URL or API availability.");
    } finally {
      setIsLoading(false);
    }
  };

  const displayData = scanResult || placeholderData;

  const headerText = scanResult
    ? `Scan Results for ${displayData.url}`
    : "Darkweb Intelligence Console";

  const dataReady = !!scanResult;

  const badgeStyle = displayData.pgpDetected
    ? "bg-neon-green/15 text-neon-green border-neon-green/40"
    : "bg-white/5 text-gray-400 border-white/10";

  const contentChangeStyle = displayData.contentChanged
    ? "text-neon-yellow"
    : "text-gray-400";

  const sectionCards = useMemo(
    () => [
      { label: "Category", value: displayData.category },
      { label: "PGP Detected", value: displayData.pgpDetected ? "Yes" : "No" },
      { label: "Content Changed", value: displayData.contentChanged ? "Yes" : "No" }
    ],
    [displayData]
  );

  return (
    <div className="min-h-screen px-6 py-12 lg:px-16">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-neon-green">Cyber Threat Monitor</p>
          <h1 className="text-3xl font-semibold md:text-4xl">{headerText}</h1>
          <p className="text-sm text-gray-400">
            Real-time signals, behavioral markers, and intelligence indicators for onion services.
          </p>
        </header>

        {!dataReady && !isLoading && (
          <div className="flex min-h-[50vh] items-center justify-center">
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
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
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
              <div className="grid gap-6 md:grid-cols-2">
                <StatusCard status={displayData.status} />
                <ThreatScoreCard score={displayData.threatScore} />
              </div>
            </div>

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
                    displayData.emails.map((email) => <li key={email}>{email}</li>)
                  ) : (
                    <li className="text-gray-500">No emails detected.</li>
                  )}
                </ul>
              </div>
              <div className="rounded-xl border border-white/10 bg-gray-900/50 p-6">
                <p className="text-sm font-semibold">Crypto Addresses</p>
                <ul className="mt-4 space-y-2 text-sm text-gray-300">
                  {displayData.cryptoAddresses?.length ? (
                    displayData.cryptoAddresses.map((address) => <li key={address}>{address}</li>)
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
