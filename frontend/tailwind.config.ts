import type { Config } from "tailwindcss";

const v = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  darkMode: ["selector", '[data-theme="dark"]'],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: v("bg"), panel: v("panel"), panel2: v("panel2"), line: v("line"),
        ink: v("ink"), mute: v("mute"), accent: v("accent"),
        home: v("home"),   // verde = local (siempre acompañado de texto, no solo color)
        away: v("away"),   // rojo = visitante
        draw: v("draw"), good: v("good"), bad: v("bad"),
      },
      fontFamily: { sans: ["system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"] },
    },
  },
  plugins: [],
};
export default config;
