// src/theme.ts — color constants for this project
// Generated once during /cli:new based on the theme you chose.
// All files import THEME from here — never hardcode ANSI codes elsewhere.
//
// To switch themes: change ACTIVE_THEME below and run bun hud.

type Theme = {
  accent:  string  // primary brand color (logo, highlights, spinner)
  fg:      string  // active/selected text
  muted:   string  // labels, hints, secondary text
  success: string  // done / ok / pass
  warn:    string  // caution, partial
  error:   string  // fail / missing
  reset:   string  // always \x1b[0m
}

// ── Theme definitions ─────────────────────────────────────────────────────────

const THEMES = {
  propane: {
    accent:  '\x1b[38;5;208m', // orange
    fg:      '\x1b[97m',       // bright white
    muted:   '\x1b[90m',       // dark gray
    success: '\x1b[32m',       // green
    warn:    '\x1b[33m',       // yellow
    error:   '\x1b[31m',       // red
    reset:   '\x1b[0m',
  },
  ocean: {
    accent:  '\x1b[36m',       // cyan
    fg:      '\x1b[97m',
    muted:   '\x1b[34m',       // dark blue
    success: '\x1b[96m',       // bright cyan
    warn:    '\x1b[33m',
    error:   '\x1b[31m',
    reset:   '\x1b[0m',
  },
  forest: {
    accent:  '\x1b[32m',       // green
    fg:      '\x1b[97m',
    muted:   '\x1b[90m',
    success: '\x1b[92m',       // bright green
    warn:    '\x1b[33m',       // amber
    error:   '\x1b[31m',
    reset:   '\x1b[0m',
  },
  neon: {
    accent:  '\x1b[95m',       // hot pink
    fg:      '\x1b[92m',       // electric green
    muted:   '\x1b[90m',
    success: '\x1b[92m',
    warn:    '\x1b[93m',       // bright yellow
    error:   '\x1b[91m',       // bright red
    reset:   '\x1b[0m',
  },
  minimal: {
    accent:  '\x1b[97m',       // white
    fg:      '\x1b[97m',
    muted:   '\x1b[2m',        // dim
    success: '\x1b[97m',
    warn:    '\x1b[2m',
    error:   '\x1b[97m',
    reset:   '\x1b[0m',
  },
} as const

// ── Active theme ──────────────────────────────────────────────────────────────
// Swap this to change the whole tool's color scheme.

const ACTIVE_THEME = 'propane' as keyof typeof THEMES

export const THEME: Theme = THEMES[ACTIVE_THEME]
