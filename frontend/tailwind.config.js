/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        border: "var(--border)",
        text: "var(--text)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        accentSoft: "var(--accent-soft)",
        danger: "var(--danger)",
      },
      fontFamily: {
        display: ["'Sora'", "sans-serif"],
        body: ["'Instrument Sans'", "sans-serif"],
      },
    },
  },
  plugins: [],
}

