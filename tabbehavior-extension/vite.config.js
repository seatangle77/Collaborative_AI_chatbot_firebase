import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { viteStaticCopy } from 'vite-plugin-static-copy'

export default defineConfig({
  plugins: [
    vue(),
    viteStaticCopy({
      targets: [
        { src: 'src/content.js', dest: 'src' }, // 保留内容脚本复制
        { src: 'src/background.js', dest: 'src' },
        { src: 'src/firebase.js', dest: 'src' }
      ]
    })
  ],
  build: {
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'popup.html'),
        detail: resolve(__dirname, 'src/detail/index.html')
      }
    },
    outDir: 'dist',
    emptyOutDir: true
  }
})
