// src/models.ts — single source of truth for all model IDs
// Never hardcode model strings anywhere else in the project.
//
// Tiers (use only what your project needs):
//   fast  — cheap, quick tasks: routing, classification, short extraction
//   smart — capable, complex tasks: generation, analysis, long context
//   write — best quality: final copy, creative output (Opus, most expensive)

export const MODELS = {
  fast:  { id: 'claude-haiku-4-5-20251001', maxTokens: 2048 },
  smart: { id: 'claude-sonnet-4-6',         maxTokens: 8000 },
  // write: { id: 'claude-opus-4-6',          maxTokens: 4000 },
} as const

export type ModelKey = keyof typeof MODELS
