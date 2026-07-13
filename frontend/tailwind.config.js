/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#FFCB05", // MTN yellow
          dark: "#E6B800",
          ink: "#1A1A1A",
        },
        surface: "#fcfcfb",
        plane: "#f9f9f7",
        ink: {
          DEFAULT: "#0b0b0b",
          secondary: "#52514e",
          muted: "#898781",
        },
        grid: "#e1e0d9",
        series: {
          1: "#2a78d6",
          2: "#1baf7a",
          3: "#eda100",
          4: "#008300",
          5: "#4a3aa7",
          6: "#e34948",
        },
        status: {
          good: "#0ca30c",
          warning: "#fab219",
          serious: "#ec835a",
          critical: "#d03b3b",
        },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
