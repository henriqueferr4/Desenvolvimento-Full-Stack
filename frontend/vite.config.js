import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
//import apiMock from './mock/apiMock'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  // `npm run dev:mock` (ou VITE_USE_MOCK=true): responde /api com dados fictícios
  const useMock = mode === 'mock' || env.VITE_USE_MOCK === 'true'

  return {
    plugins: [react()],
    server: {
      // encaminha /api para o Flask em desenvolvimento
      proxy: useMock ? undefined : { '/api': env.VITE_PROXY_TARGET || 'http://localhost:5000' },
    },
  }
})
