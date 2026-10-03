/** One reading of the context window, taken after a main-thread turn. */
export type Reading = { tokens: number; window: number; percent: number }

/**
 * One row of /context's breakdown that the bar draws: an element occupying the
 * window (`used`) or the autocompact reserve (`buffer`), with the theme colour
 * /context draws it in. A segment stored before `kind` existed reads as `used`.
 */
export type Segment = { name: string; tokens: number; color: string; kind?: 'used' | 'buffer' }

declare module 'claude-code' {
  interface PluginState {
    'token-weather': { readings: Reading[]; segments: Segment[] }
  }
}
