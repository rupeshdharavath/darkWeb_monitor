/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "neon-green": "#00f5a0",
        "neon-red": "#ff4d4d",
        "neon-yellow": "#ffd166",
        "neon-blue": "#4cc9f0"
      },
      boxShadow: {
        "soft-glow": "0 0 20px rgba(0, 245, 160, 0.12)",
        "red-glow": "0 0 20px rgba(255, 77, 77, 0.18)",
        "yellow-glow": "0 0 20px rgba(255, 209, 102, 0.18)"
      },
      keyframes: {
        "slide-in-right": {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" }
        },
        "fade-out": {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" }
        }
      },
      animation: {
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "fade-out": "fade-out 0.3s ease-out"
      }
    }
  },
  plugins: []
};
