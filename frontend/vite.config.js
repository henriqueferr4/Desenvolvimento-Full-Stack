import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(async ({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  // `npm run dev:mock` (ou VITE_USE_MOCK=true): responde /api com dados fictícios
  const useMock = mode === 'mock' || env.VITE_USE_MOCK === 'true'

  const plugins = [react()]
  if (useMock) {
    // import dinâmico: a pasta mock/ fica fora da imagem Docker (.dockerignore),
    // então o build de produção nunca precisa dela
    //const { default: apiMock } = await import('./mock/apiMock.js')
    //plugins.push(apiMock())
  }

  return {
    plugins,
    server: {
      // encaminha /api para o Flask em desenvolvimento
      //proxy: useMock ? undefined : { '/api': env.VITE_PROXY_TARGET || 'http://localhost:5000' },
    },
  }
})