export default function Loader({ label = "Scanning" }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-neon-green/40 border-t-neon-green" />
      <p className="text-sm uppercase tracking-[0.4em] text-neon-green/80">{label}</p>
    </div>
  );
}
