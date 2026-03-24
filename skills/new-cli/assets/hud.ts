// src/hud.ts — ANSI HUD screen loop
// Replace TOOL_NAME with your project name.
// Replace HOME_MENU items with your actual commands.
// Run: bun hud

// ── ANSI helpers ──────────────────────────────────────────────────────────────

const A = {
  clear:      '\x1b[2J\x1b[H',
  hideCursor: '\x1b[?25l',
  showCursor: '\x1b[?25h',
  reset:  '\x1b[0m',
  bold:   '\x1b[1m',
  dim:    '\x1b[2m',
  gold:   '\x1b[33m',
  green:  '\x1b[32m',
  red:    '\x1b[31m',
  gray:   '\x1b[90m',
  white:  '\x1b[97m',
  cyan:   '\x1b[36m',
} as const

const w  = (s: string) => process.stdout.write(s)
const nl = () => w('\n')

// ── ASCII art header ───────────────────────────────────────────────────────────
// Generate 6-line block letters for your tool name at: patorjk.com/software/taag
// Use "ANSI Shadow" font for consistency with other Propane CLIs.

const ASCII_ART = [
  '  ████████╗ ██████╗  ██████╗ ██╗     ',
  '     ██╔══╝██╔═══██╗██╔═══██╗██║     ',
  '     ██║   ██║   ██║██║   ██║██║     ',
  '     ██║   ██║   ██║██║   ██║██║     ',
  '     ██║   ╚██████╔╝╚██████╔╝███████╗',
  '     ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝',
]

// ── Spinner ───────────────────────────────────────────────────────────────────

const FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

function spinner(label: string): { stop: () => void } {
  let i = 0
  const t = setInterval(() => {
    w(`\r${A.gold}${FRAMES[i++ % FRAMES.length]}${A.reset} ${label}`)
  }, 80)
  return { stop: () => { clearInterval(t); w('\r\x1b[K') } }
}

// ── Menu items ────────────────────────────────────────────────────────────────

interface MenuItem { label: string; desc: string }

const HOME_MENU: MenuItem[] = [
  { label: 'Run',    desc: 'Execute the main task'          },
  { label: 'Browse', desc: 'View recent output'             },
  { label: 'Config', desc: 'View and update configuration'  },
  { label: 'Exit',   desc: ''                               },
]

// ── Key reading ───────────────────────────────────────────────────────────────

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
  w(A.clear + A.hideCursor)
  w(A.gold)
  ASCII_ART.forEach(line => w(line + '\n'))
  w(A.reset)
  nl()
  HOME_MENU.forEach((item, i) => {
    const active = i === selected
    const cursor = active ? `${A.bold}${A.white}▶ ` : `${A.dim}  `
    const desc   = item.desc ? `${A.dim}${A.gray}  ${item.desc}${A.reset}` : ''
    w(`  ${cursor}${item.label}${A.reset}${desc}\n`)
  })
  nl()
  w(`${A.gray}  ↑ ↓ navigate   ↵ select   ctrl+c exit${A.reset}\n`)
}

async function screenConfig(): Promise<void> {
  w(A.clear)
  w(`${A.gold}${A.bold}  Configuration${A.reset}\n\n`)
  w(`  ${A.gray}ANTHROPIC_API_KEY${A.reset}  ${process.env.ANTHROPIC_API_KEY ? '••••set' : A.red + 'not set' + A.reset}\n`)
  nl()
  w(`${A.gray}  ← back${A.reset}\n`)
  await readKey()
}

// ── Main HUD loop ─────────────────────────────────────────────────────────────

export async function runHud(): Promise<void> {
  let selected = 0
  const UP    = '\x1b[A'
  const DOWN  = '\x1b[B'
  const ENTER = '\r'
  const CTRL_C = '\x03'

  process.on('exit', () => w(A.showCursor))
  process.on('SIGINT', () => { w(A.showCursor); process.exit(0) })

  while (true) {
    drawHome(selected)
    const key = await readKey()

    if (key === CTRL_C) { w(A.showCursor); process.exit(0) }
    if (key === UP   && selected > 0)                selected--
    if (key === DOWN && selected < HOME_MENU.length - 1) selected++

    if (key === ENTER) {
      const choice = HOME_MENU[selected].label
      if (choice === 'Exit') { w(A.showCursor); process.exit(0) }
      if (choice === 'Config') { await screenConfig(); continue }
      if (choice === 'Run') {
        w(A.clear)
        const s = spinner('Running...')
        await new Promise(r => setTimeout(r, 1000)) // replace with real work
        s.stop()
        w(`${A.green}  ✓ Done${A.reset}\n`)
        await readKey()
      }
    }
  }
}
