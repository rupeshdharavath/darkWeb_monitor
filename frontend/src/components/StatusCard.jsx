const statusStyles = {
  ONLINE: "border-neon-green/40 text-neon-green shadow-soft-glow",
  OFFLINE: "border-neon-red/40 text-neon-red shadow-red-glow",
  TIMEOUT: "border-neon-yellow/40 text-neon-yellow shadow-yellow-glow"
};

export default function StatusCard({ status }) {
  const normalized = status?.toUpperCase() || "UNKNOWN";
  const style = statusStyles[normalized] || "border-white/10 text-gray-300";

  return (
    <div className={`rounded-xl border bg-gray-900/50 p-6 ${style}`}>
      <p className="text-xs uppercase tracking-[0.3em] text-gray-400">Status</p>
      <p className="mt-4 text-3xl font-semibold tracking-wide">{normalized}</p>
    </div>
  );
}
