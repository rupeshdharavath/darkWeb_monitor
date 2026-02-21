import { useState } from "react";

export default function SearchBar({ onSearch, isLoading }) {
  const [value, setValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!value.trim() || isLoading) return;
    onSearch(value.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-2xl flex-col gap-4">
      <label className="text-sm uppercase tracking-[0.3em] text-gray-400">
        Onion URL
      </label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          type="text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="http://exampleonion.onion"
          className="flex-1 rounded-xl border border-white/10 bg-gray-900/60 px-4 py-3 text-base text-gray-100 outline-none transition focus:border-neon-blue/70 focus:ring-2 focus:ring-neon-blue/30"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-xl border border-neon-green/40 bg-neon-green/20 px-6 py-3 text-sm font-semibold uppercase tracking-[0.2em] text-neon-green transition hover:bg-neon-green/30 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? "Scanning" : "Search"}
        </button>
      </div>
    </form>
  );
}
