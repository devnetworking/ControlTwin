/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ot: {
          bg: "#0A1628",
          card: "#0F1F3D",
          border: "#1B3A6B",
          blue: "#00A8E8",
          orange: "#F4A020",
          green: "#2ECC71",
          red: "#E74C3C",
          gray: "#6B7280"
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"]
      }
    }
  },
  plugins: []
};
