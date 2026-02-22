import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      fontSize: {
        "chat-title": ["20px", { fontWeight: "600" }],
        message: ["15px", { lineHeight: "1.6", fontWeight: "400" }],
        debug: ["13px", { fontWeight: "400" }],
        timestamp: ["12px", { fontWeight: "400" }],
      },
    },
  },
  plugins: [],
};

export default config;
