export const MODELS = {
  fast:  { id: 'claude-haiku-4-5-20251001', maxTokens: 2048 },
  smart: { id: 'claude-sonnet-4-6',         maxTokens: 8000 },
} as const
export type ModelTier = keyof typeof MODELS
