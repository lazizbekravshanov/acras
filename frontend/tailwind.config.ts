import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        severity: {
          minor: "#3b82f6",
          moderate: "#f59e0b",
          severe: "#f97316",
          critical: "#ef4444",
        },
        surface: {
          DEFAULT: "#0a0a0f",
          card: "#111119",
          elevated: "#1a1a25",
          border: "#2a2a3a",
        },
        accent: {
          DEFAULT: "#6366f1",
          hover: "#818cf8",
        },
      },
    },
  },
  plugins: [],
};

export default config;
