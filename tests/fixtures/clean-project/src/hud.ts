import { MODELS } from './models'
import { THEME as T } from './theme'

const cols = () => Math.min(process.stdout.columns ?? 80, 66)

function redraw() {
  process.stdout.write('\x1b[2J\x1b[H')
  process.stdout.write(`${T.accent}Dashboard${T.reset}\n`)
  process.stdout.write(`${T.muted}Model: ${MODELS.fast.id}${T.reset}\n`)
}

process.stdout.on('resize', redraw)
redraw()
