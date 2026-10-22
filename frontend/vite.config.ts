import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      // Catalogue photos live at /products/<file>.jpg. The shop pages use
      // /products and /products/<id>, so only image files go to the API.
      '/products': {
        target: 'http://127.0.0.1:8000',
        bypass(req) {
          const path = (req.url ?? '').split('?')[0]
          if (!/\.(jpg|jpeg|png|webp|gif)$/i.test(path)) {
            return '/index.html'
          }
        },
      },
    },
  },
})
