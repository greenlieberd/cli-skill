// src/models.ts — single source of truth for all model IDs
// Never hardcode model strings anywhere else in the project.
//
// Semantic roles — pick the tiers your project needs:
//   fast  — Haiku: cheap, high-volume — routing, classification, quick extraction
//   smart — Sonnet: capable — generation, analysis, long context, most tasks
//   write — Opus: best quality — final copy, creative output (most expensive)
//
// The scaffold includes only the tiers you chose during planning.
// Add tiers here if you upgrade — update callers to use the new key.

export const MODELS = {
  fast:  { id: 'claude-haiku-4-5-20251001', maxTokens: 2048 },
  smart: { id: 'claude-sonnet-4-6',         maxTokens: 8000 },
  write: { id: 'claude-opus-4-6',           maxTokens: 4000 },
} as const

export type ModelTier = keyof typeof MODELS
