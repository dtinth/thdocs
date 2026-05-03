import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [tailwindcss()],
  build: {
    outDir: resolve(__dirname, "../src/thdocs/static"),
    emptyOutDir: false,
    sourcemap: true,
    lib: {
      entry: resolve(__dirname, "src/main.ts"),
      name: "thdocs",
      formats: ["umd"],
      fileName: () => "thdocs.js",
    },
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) return "thdocs.css";
          return "[name][extname]";
        },
      },
    },
  },
});
