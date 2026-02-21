const getRiskTone = (score) => {
  if (score >= 75) return "text-neon-red border-neon-red/40 shadow-red-glow";
  if (score >= 40) return "text-neon-yellow border-neon-yellow/40 shadow-yellow-glow";
  return "text-neon-green border-neon-green/40 shadow-soft-glow";
};

export default function ThreatScoreCard({ score = 0 }) {
  return (
    <div className={`rounded-xl border bg-gray-900/50 p-6 ${getRiskTone(score)}`}>
      <p className="text-xs uppercase tracking-[0.3em] text-gray-400">Threat Score</p>
      <p className="mt-4 text-5xl font-semibold">{score}</p>
      <p className="mt-2 text-sm text-gray-400">Risk calculated from signals</p>
    </div>
  );
}
