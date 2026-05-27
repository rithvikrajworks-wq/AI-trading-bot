/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080c14",
        foreground: "#f8fafc",
        card: {
          DEFAULT: "rgba(13, 21, 39, 0.6)",
          border: "rgba(51, 65, 85, 0.3)",
          hover: "rgba(20, 31, 58, 0.8)",
        },
        muted: {
          DEFAULT: "#64748b",
          foreground: "#94a3b8",
        },
        accent: {
          buy: {
            DEFAULT: "#10b981", // Emerald Green
            glow: "rgba(16, 185, 129, 0.15)",
          },
          sell: {
            DEFAULT: "#ef4444", // Rose Red
            glow: "rgba(239, 68, 68, 0.15)",
          },
          hold: {
            DEFAULT: "#f59e0b", // Amber Yellow
            glow: "rgba(245, 158, 11, 0.15)",
          },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      animation: {
        "shimmer": "shimmer 2s infinite linear",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
}
