// Pure forecasting helpers: no `$`, so the tests can call them directly.
import type { Reading, Segment } from '../types'

/**
 * The breakdown's `used` rows, largest first, then its `buffer` rows, each
 * keeping the theme colour /context draws it in. Free space is derived, not
 * stored, and deferred schemas sit outside the window, so both are left out.
 */
export function toSegments(
  categories: readonly { name: string; tokens: number; kind: string; color: string }[],
): Segment[] {
  const rows = (kind: 'used' | 'buffer') =>
    categories
      .filter(c => c.kind === kind && c.tokens > 0)
      .map(c => ({ name: c.name, tokens: c.tokens, color: c.color, kind }))
  return [...rows('used').sort((a, b) => b.tokens - a.tokens), ...rows('buffer')]
}

export function isBuffer(s: Segment): boolean {
  return s.kind === 'buffer'
}

/** An element's share of the window as a whole percentage; "<1%" for a sliver. */
export function share(tokens: number, window: number): string {
  if (window <= 0) return '0%'
  const p = (tokens / window) * 100
  return p > 0 && p < 1 ? '<1%' : `${Math.round(p)}%`
}

/**
 * One segment of the bar, exactly `cells` wide. It is drawn as a filled
 * background, so the text is spaces with the percentage centred in it when it
 * fits with a cell of margin either side, and spaces alone when it does not.
 */
export function segmentText(cells: number, percent: string): string {
  const n = Math.max(0, cells)
  if (n < percent.length + 2) return ' '.repeat(n)
  const left = Math.floor((n - percent.length) / 2)
  return ' '.repeat(left) + percent + ' '.repeat(n - left - percent.length)
}

/**
 * A segment's text: the first candidate that fits with a cell of margin either
 * side, centred; blank when none fits. Always exactly `cells` wide.
 */
export function fitText(cells: number, candidates: readonly string[]): string {
  const n = Math.max(0, cells)
  return segmentText(n, candidates.find(c => n >= c.length + 2) ?? '')
}

/**
 * The free segment: the room left before autocompact fires, longest wording
 * that fits ("19% left before autocompact", "19% left", "19%"), blank otherwise.
 */
export function freeText(cells: number, tokens: number, window: number): string {
  const pct = share(Math.max(0, tokens), window)
  return fitText(cells, [`${pct} left before autocompact`, `${pct} left`, pct])
}

/**
 * The autocompact buffer: a fixed reserve, so its size says nothing about the
 * session. It is named, not measured, and left blank when the name does not fit.
 */
export function bufferText(cells: number): string {
  return fitText(cells, ['autocompact'])
}

/** Window left once the used content and the autocompact buffer are taken out. */
export function freeTokens(window: number, used: number, buffer: number): number {
  return Math.max(0, window - used - buffer)
}

/** The bar's cells for a band `columns` wide: the full width less one, at least 1. */
export function barWidth(columns: number): number {
  return Math.max(1, Math.floor(columns) - 1)
}

/**
 * Cells of a `width`-wide bar each segment fills, scaled to the window. Every
 * non-empty segment gets at least one cell while room remains, so a small
 * element still shows its colour; the rest of the bar is free space.
 */
export function barCells(segments: readonly Segment[], window: number, width: number): number[] {
  if (window <= 0 || width <= 0) return segments.map(() => 0)
  let left = width
  return segments.map(s => {
    const want = Math.max(1, Math.round((s.tokens / window) * width))
    const cells = Math.min(left, want)
    left -= cells
    return cells
  })
}

export const HISTORY = 12

// Braille, filled from the bottom up. Block elements (▁…█) sat flush on the bar's filled row
// below and fused with it into one stretched slab; braille dots keep their gaps.
const LEVELS = ['⣀', '⣤', '⣶', '⣿']

export type Forecast = { upTo: number; icon: string; word: string; color: string }

export const FORECAST: readonly Forecast[] = [
  { upTo: 25, icon: '☀', word: 'Clear', color: 'yellow' },
  { upTo: 50, icon: '☁', word: 'Cloudy', color: 'cyan' },
  { upTo: 75, icon: '☂', word: 'Showers', color: 'blue' },
  { upTo: 90, icon: '☇', word: 'Storm', color: 'magenta' },
  { upTo: Infinity, icon: '↯', word: 'Compact soon', color: 'red' },
]

export function forecast(percent: number): Forecast {
  return FORECAST.find(f => percent < f.upTo) ?? FORECAST[FORECAST.length - 1]!
}

/** A reading from the engine's context figures, or null before the window is known. */
export function toReading(context: { tokens?: number; window: number; percent?: number }): Reading | null {
  if (!context.window) return null
  const tokens = context.tokens ?? 0
  const percent = context.percent ?? Math.round((tokens / context.window) * 100)
  return { tokens, window: context.window, percent }
}

/** Append a reading, skipping an unchanged repeat, keeping the last HISTORY. */
export function push(history: readonly Reading[], r: Reading): Reading[] {
  const last = history[history.length - 1]
  if (last && last.tokens === r.tokens && last.window === r.window) return [...history]
  return [...history, r].slice(-HISTORY)
}

/**
 * One glyph per reading, scaled to the history's own low and high, so the trend shows even
 * while every reading sits near one level (the percentage beside it gives the absolute).
 * A flat history is a flat low line.
 */
export function spark(history: readonly Reading[]): string {
  const tokens = history.map(r => r.tokens)
  const low = Math.min(...tokens)
  const range = Math.max(...tokens) - low
  return tokens
    .map(t => LEVELS[range > 0 ? Math.min(LEVELS.length - 1, Math.floor(((t - low) / range) * LEVELS.length)) : 0])
    .join('')
}

/** Tokens the last turn added, or null with fewer than two readings. */
export function added(history: readonly Reading[]): number | null {
  const now = history[history.length - 1]
  const before = history[history.length - 2]
  return now && before ? now.tokens - before.tokens : null
}

export function short(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`
  if (Math.abs(n) >= 1_000) return `${Math.round(n / 1_000)}k`
  return String(n)
}
