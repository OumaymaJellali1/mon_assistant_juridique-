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
        primary: "#1D4ED8",   
        secondary: "#374151", 
        accent: "#10B981",    
        background: "#F9FAFB", 
        foreground: "#111827", 
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"], 
        serif: ["Merriweather", "serif"],
      },
      boxShadow: {
        soft: "0 4px 6px rgba(0,0,0,0.1)",
        strong: "0 6px 12px rgba(0,0,0,0.15)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"), 
    require("@tailwindcss/aspect-ratio"), 
  ],
};

export default config;
