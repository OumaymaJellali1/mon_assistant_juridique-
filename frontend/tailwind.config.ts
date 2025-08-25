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
        primary: "#1D4ED8",   // Bleu professionnel
        secondary: "#374151", // Gris foncé
        accent: "#10B981",    // Vert (highlights)
        background: "#F9FAFB", // Fond clair
        foreground: "#111827", // Texte sombre
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"], // Police moderne
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
    require("@tailwindcss/forms"), // Pour les inputs et formulaires
    require("@tailwindcss/typography"), // Pour un beau rendu des textes
    require("@tailwindcss/aspect-ratio"), // Pour gérer les images/vidéos
  ],
};

export default config;
