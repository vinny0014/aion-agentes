/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ice: "#08080F",        /* fundo escuro */
        ink: "#ECECF4",        /* texto claro */
        surface: "#111119",    /* cartões */
        line: "rgba(255,255,255,0.08)",
        ultra: "#8B5CF6",      /* violeta primário */
        signal: "#C084FC",     /* violeta claro / live */
        slateui: "#9CA0B4",
      },
      fontFamily: {
        display: ["ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        body: ["ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "Liberation Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
