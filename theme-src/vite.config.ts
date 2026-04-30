import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [tailwindcss()],
  build: {
    outDir: resolve(__dirname, "../src/thdocs/static"),
    emptyOutDir: false,
    rollupOptions: {
      input: { thdocs: resolve(__dirname, "src/main.ts") },
      output: {
        entryFileNames: "thdocs.js",
        chunkFileNames: "thdocs-[name].js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) return "thdocs.css";
          return "[name][extname]";
        },
      },
    },
  },
});
