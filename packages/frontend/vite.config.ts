import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: true, // Ensures Docker handles file change notifications correctly
    },
    host: "0.0.0.0", // Makes the server accessible outside the container
    port: 8000, // Ensure the port matches the exposed one
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
