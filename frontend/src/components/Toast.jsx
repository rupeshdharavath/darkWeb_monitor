import { useEffect } from "react";

const Toast = ({ message, type = "success", onClose, duration = 3000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const typeStyles = {
    success: "bg-neon-green/20 border-neon-green text-neon-green",
    error: "bg-neon-red/20 border-neon-red text-neon-red",
    info: "bg-neon-blue/20 border-neon-blue text-neon-blue",
    warning: "bg-neon-yellow/20 border-neon-yellow text-neon-yellow"
  };

  const icons = {
    success: "✓",
    error: "✕",
    info: "ℹ",
    warning: "⚠"
  };

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${typeStyles[type]} shadow-lg backdrop-blur-sm animate-slide-in-right`}
      style={{ minWidth: "300px", maxWidth: "500px" }}
    >
      <span className="text-xl font-bold">{icons[type]}</span>
      <span className="flex-1 text-sm font-medium">{message}</span>
      <button
        onClick={onClose}
        className="text-current opacity-70 hover:opacity-100 transition-opacity"
      >
        ✕
      </button>
    </div>
  );
};

export default Toast;
