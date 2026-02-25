import { Link, useLocation } from "react-router-dom";

export default function Header() {
  const location = useLocation();
  const isHistory = location.pathname === "/history";
  const isDashboard = location.pathname === "/" || location.pathname.startsWith("/entry/");

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-neon-green/10 border border-neon-green/30">
            <svg className="h-6 w-6 text-neon-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold">Darkweb Monitor</h1>
            <p className="text-xs text-gray-500">Threat Intelligence Platform</p>
          </div>
        </Link>

        <nav className="flex items-center gap-4">
          <Link
            to="/"
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              isDashboard
                ? "bg-neon-green/10 text-neon-green border border-neon-green/30"
                : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
            }`}
          >
            Dashboard
          </Link>
          <Link
            to="/history"
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              isHistory
                ? "bg-neon-green/10 text-neon-green border border-neon-green/30"
                : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
            }`}
          >
            History
          </Link>
        </nav>
      </div>
    </header>
  );
}
