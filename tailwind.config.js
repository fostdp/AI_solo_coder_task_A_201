/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        bronze: {
          50: "#fbf3e1",
          100: "#f5e0b0",
          200: "#e9c878",
          300: "#d4af37",
          400: "#c49a2a",
          500: "#b87333",
          600: "#8a5a25",
          700: "#66421a",
          800: "#3d2810",
          900: "#1f1408",
          950: "#0d0904",
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', '"Source Han Serif SC"', "serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      boxShadow: {
        bronze: "0 0 24px rgba(212, 175, 55, 0.25)",
        "bronze-lg": "0 0 48px rgba(212, 175, 55, 0.35)",
      },
    },
  },
  plugins: [],
};
