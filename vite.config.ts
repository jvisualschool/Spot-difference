import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// https://vitejs.dev/config/
export default defineConfig({
  base: '/FINDSPOT/',
  plugins: [
    react(),
    {
      name: 'puzzle-admin-api',
      configureServer(server) {
        server.middlewares.use(async (req, res, next) => {
          if (req.url === '/save-puzzle' && req.method === 'POST') {
            let body = ''
            req.on('data', chunk => {
              body += chunk.toString()
            })
            req.on('end', () => {
              try {
                const data = JSON.parse(body)
                const puzzleId = data.puzzle_id
                if (!puzzleId) {
                  res.statusCode = 400
                  res.end('Missing puzzle_id')
                  return
                }

                const baseDir = __dirname
                const answerPath = path.join(baseDir, 'public', 'puzzles', puzzleId, 'answer.json')

                // 1. Save the updated answer.json
                fs.writeFileSync(answerPath, JSON.stringify(data, null, 4), 'utf-8')

                // 2. Update manifest.json
                const manifestPath = path.join(baseDir, 'public', 'puzzles', 'manifest.json')
                if (fs.existsSync(manifestPath)) {
                  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'))
                  for (const p of manifest.puzzles || []) {
                    if (p.id === puzzleId) {
                      p.differences = data.total_differences
                      break
                    }
                  }
                  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8')
                }

                res.statusCode = 200
                res.setHeader('Content-Type', 'application/json')
                res.end(JSON.stringify({ status: 'success' }))
                console.log(`✅ Saved puzzle ${puzzleId} and updated manifest via Vite.`)
              } catch (e) {
                console.error(`❌ Error saving puzzle: ${e}`)
                res.statusCode = 500
                res.end(String(e))
              }
            })
          } else {
            next()
          }
        })
      }
    }
  ],
  build: {
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        game: path.resolve(__dirname, 'game.html'),
        admin: path.resolve(__dirname, 'admin_dashboard.html'),
      },
    },
  },
})
