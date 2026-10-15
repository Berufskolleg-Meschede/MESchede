import { spawn } from 'node:child_process'
import { createRequire } from 'node:module'

// Eigener Produktionsbuild für Browserprüfungen; kein Hot Reload und kein Zugriff auf den Entwicklungsbuild.
const require = createRequire(import.meta.url)
const next = require.resolve('next/dist/bin/next')
const env = { ...process.env, MES_NEXT_DIST_DIR: '.next/issue30-tests' }
let stopping = false
let child = spawn(process.execPath, [next, 'build', '--webpack'], { env, stdio: 'inherit' })

function stop(signal) {
  stopping = true
  child.kill(signal)
}
process.on('SIGTERM', () => stop('SIGTERM'))
process.on('SIGINT', () => stop('SIGINT'))

child.once('exit', code => {
  if (stopping || code !== 0) { process.exit(code ?? 1) }
  child = spawn(process.execPath, [next, 'start', '--hostname', '127.0.0.1', '--port', '3029'], { env, stdio: 'inherit' })
  child.once('exit', result => process.exit(result ?? 0))
})
