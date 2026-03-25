// src/hud.ts — ANSI HUD screen loop
// Adapt for your project:
//   - Replace ASCII_ART with your tool's block letter logo
//   - Replace HOME_MENU items with your actual v0.1 commands
//   - Import THEME from src/theme.ts (generated per project)
// Run: bun hud

import { THEME as T } from './theme.ts'

// ── ANSI helpers ──────────────────────────────────────────────────────────────

const A = {
  clear:      '\x1b[2J\x1b[H',
  hideCursor: '\x1b[?25l',
  showCursor: '\x1b[?25h',
  reset:      '\x1b[0m',
  bold:       '\x1b[1m',
  dim:        '\x1b[2m',
} as const

const w    = (s: string) => process.stdout.write(s)
const nl   = () => w('\n')
const cols = () => Math.min(process.stdout.columns ?? 80, 66)

// ── ASCII art logo ─────────────────────────────────────────────────────────────
// Replace with 6-line block letters for your tool name.
// Font: "ANSI Shadow" at patorjk.com/software/taag
// Shown only when terminal is wide enough (≥ 48 cols).

const ASCII_ART = [
  '  ████████╗ ██████╗  ██████╗ ██╗     ',
  '     ██╔══╝██╔═══██╗██╔═══██╗██║     ',
  '     ██║   ██║   ██║██║   ██║██║     ',
  '     ██║   ██║   ██║██║   ██║██║     ',
  '     ██║   ╚██████╔╝╚██████╔╝███████╗',
  '     ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝',
]

function drawLogo(): void {
  if (cols() < 48) {
    w(`${T.accent}${A.bold}  TOOL${A.reset}\n`)
    return
  }
  w(T.accent)
  ASCII_ART.forEach(line => w(line + '\n'))
  w(A.reset)
}

// ── Spinner ────────────────────────────────────────────────────────────────────

const FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

function spinner(label: string): { stop: () => void } {
  let i = 0
  const t = setInterval(() => {
    w(`\r${T.accent}${FRAMES[i++ % FRAMES.length]}${A.reset} ${label}`)
  }, 80)
  return { stop: () => { clearInterval(t); w('\r\x1b[K') } }
}

// ── Menu ───────────────────────────────────────────────────────────────────────

interface MenuItem { label: string; desc: string }

const HOME_MENU: MenuItem[] = [
  { label: 'Run',    desc: 'Execute the main task'         },
  { label: 'Browse', desc: 'View recent output'            },
  { label: 'Config', desc: 'View configuration'           },
  { label: 'Exit',   desc: ''                              },
]

// ── Key input ─────────────────────────────────────────────────────────────────

async function readKey(): Promise<string> {
  process.stdin.setRawMode(true)
  process.stdin.resume()
  return new Promise(resolve => {
    process.stdin.once('data', buf => {
      process.stdin.setRawMode(false)
      process.stdin.pause()
      resolve(buf.toString())
    })
  })
}

// ── Screens ───────────────────────────────────────────────────────────────────

function drawHome(selected: number): void {
  const c = cols()

  if (c < 50) {
    w(A.clear + A.hideCursor)
    w(`${T.muted}  Terminal too narrow (${c} cols). Widen to 50+ to use this tool.${A.reset}\n`)
    return
  }

  w(A.clear + A.hideCursor)
  nl()
  drawLogo()
  nl()

  HOME_MENU.forEach((item, i) => {
    const active = i === selected
    const cursor = active ? `${A.bold}${T.fg}▶ ` : `${A.dim}  `
    const desc   = item.desc ? `${T.muted}  ${item.desc}${A.reset}` : ''
    w(`  ${cursor}${item.label}${A.reset}${desc}\n`)
  })

  nl()
  w(`${T.muted}  ↑ ↓ navigate   ↵ select   ctrl+c exit${A.reset}\n`)
}

async function screenConfig(): Promise<void> {
  w(A.clear)
  w(`${T.accent}${A.bold}  Configuration${A.reset}\n\n`)
  w(`  ${T.muted}ANTHROPIC_API_KEY${A.reset}  ${
    process.env.ANTHROPIC_API_KEY ? T.success + '••••set' : T.error + 'not set'
  }${A.reset}\n`)
  nl()
  w(`${T.muted}  any key to go back${A.reset}\n`)
  await readKey()
}

// ── Main HUD loop ─────────────────────────────────────────────────────────────

export async function runHud(): Promise<void> {
  let selected = 0
  const UP     = '\x1b[A'
  const DOWN   = '\x1b[B'
  const ENTER  = '\r'
  const CTRL_C = '\x03'

  const exit = () => { w(A.showCursor); process.exit(0) }
  process.on('exit',   () => w(A.showCursor))
  process.on('SIGINT', exit)

  // ── Resize handler — required for all ANSI HUDs ──
  process.stdout.on('resize', () => drawHome(selected))

  while (true) {
    drawHome(selected)
    const key = await readKey()

    if (key === CTRL_C) exit()
    if (key === UP   && selected > 0)                    selected--
    if (key === DOWN && selected < HOME_MENU.length - 1) selected++

    if (key === ENTER) {
      const choice = HOME_MENU[selected].label
      if (choice === 'Exit')   exit()
      if (choice === 'Config') { await screenConfig(); continue }
      if (choice === 'Browse') {
        // Replace with: open output browser, show file list, etc.
        w(A.clear)
        w(`${T.muted}  No output yet.${A.reset}\n\n`)
        w(`${T.muted}  any key to go back${A.reset}\n`)
        await readKey()
      }
      if (choice === 'Run') {
        w(A.clear)
        const s = spinner('Running…')
        await new Promise(r => setTimeout(r, 1000)) // replace with real work
        s.stop()
        w(`${T.success}  ✓ Done${A.reset}\n\n`)
        w(`${T.muted}  any key to go back${A.reset}\n`)
        await readKey()
      }
    }
  }
}
