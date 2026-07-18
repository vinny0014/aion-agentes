import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = "http://localhost:8000";
const proxy = {
  "/api": backend,
  "/robots.txt": backend,
  "/sitemap.xml": backend,
  "/news-sitemap.xml": backend,
  "/image-sitemap.xml": backend,
  "/rss.xml": backend,
  "/favicon.png": backend,
  "/icon-192.png": backend,
  "/icon-512.png": backend,
};

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
