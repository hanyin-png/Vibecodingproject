import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // 开发时代理：前端里访问 /api/xxx 会被转发到本机 8000 端口的 FastAPI 后端
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
