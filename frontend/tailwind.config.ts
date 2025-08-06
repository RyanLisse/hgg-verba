import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  safelist: [
    // Dynamically constructed classes that might be missed by purging
    "bg-yellow-300",
    "bg-gray-300",
    "bg-gray-400",
    "bg-zinc-300",
    "bg-zinc-400",
    "bg-red-300",
    "bg-green-300",
    "bg-cyan-300",
    "bg-fuchsia-300",
    "bg-yellow-400",
    "bg-green-400",
    "bg-cyan-400",
    "bg-fuchsia-400",
    "bg-red-400",
    "bg-indigo-400",
  ],
  plugins: [require("@tailwindcss/typography")],
};

export default config;
