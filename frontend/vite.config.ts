import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Mock build (`vite build --mode mock`, see `npm run build:mock`): a static bundle
// in dist-mock/ that needs no backend. Relative base + classic (non-module)
// script so index.html can also be opened from file:// (module scripts are
// blocked there by the browser).
function classicScript(): Plugin {
  return {
    name: "dalel-classic-script",
    enforce: "post",
    transformIndexHtml(html) {
      return html.replace(/<script type="module" crossorigin/g, "<script defer");
    },
  };
}

// Dev server on 5173; /api is proxied to the FastAPI backend on 127.0.0.1:8000.
export default defineConfig(({ mode, command }) => {
  const mock = mode === "mock";
  return {
    base: mock && command === "build" ? "./" : "/",
    plugins: [react(), tailwindcss(), ...(mock ? [classicScript()] : [])],
    build: mock
      ? {
          outDir: "dist-mock",
          emptyOutDir: true,
          rollupOptions: {
            output: { format: "iife" as const, inlineDynamicImports: true },
          },
        }
      : undefined,
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
