import { expect, test } from 'claude-code/testing'
import type { ContextCategory, SessionContextBreakdown } from 'claude-code'

import { HISTORY, added, barCells, barWidth, forecast, freeTokens, push, segmentText, freeText, bufferText, share, short, spark, toReading, toSegments } from './weather'

const BAND_PROPS = {
  hasSurvey: false,
  isWorking: false,
  maxRows: 10,
  bodyColumns: 100,
  scroll: { offset: 0, bodyRows: 10 },
  view: {},
}

const ROWS: ContextCategory[] = [
  { name: 'System prompt', tokens: 12_000, kind: 'used', color: 'promptBorder', isDeferred: false },
  { name: 'Messages', tokens: 120_000, kind: 'used', color: 'permission', isDeferred: false },
  { name: 'MCP tools', tokens: 30_000, kind: 'used', color: 'inactive', isDeferred: false },
  { name: 'Free space', tokens: 38_000, kind: 'free', color: 'inactive', isDeferred: false },
  { name: 'Autocompact buffer', tokens: 45_000, kind: 'buffer', color: 'inactive', isDeferred: false },
  { name: 'Deferred tools', tokens: 9_000, kind: 'deferred', color: 'inactive', isDeferred: true },
]

test('segments keep used rows largest first, then the buffer', () => {
  expect(toSegments(ROWS)).toEqual([
    { name: 'Messages', tokens: 120_000, color: 'permission', kind: 'used' },
    { name: 'MCP tools', tokens: 30_000, color: 'inactive', kind: 'used' },
    { name: 'System prompt', tokens: 12_000, color: 'promptBorder', kind: 'used' },
    { name: 'Autocompact buffer', tokens: 45_000, color: 'inactive', kind: 'buffer' },
  ])
  expect(toSegments([{ name: 'Empty', tokens: 0, kind: 'used', color: 'text' }])).toEqual([])
})

test('bar cells scale to the window and never overflow the width', () => {
  const segs = toSegments(ROWS)
  // The buffer comes last and gets what the used rows leave of the width.
  expect(barCells(segs, 200_000, 50)).toEqual([30, 8, 3, 9])
  const tiny = [{ name: 'a', tokens: 1, color: 'x' }, { name: 'b', tokens: 1, color: 'y' }]
  expect(barCells(tiny, 1_000_000, 10)).toEqual([1, 1])
  const big = [{ name: 'a', tokens: 900, color: 'x' }, { name: 'b', tokens: 900, color: 'y' }]
  expect(barCells(big, 1_000, 10).reduce((a, b) => a + b, 0)).toBe(10)
})


test('forecast follows the blog thresholds', () => {
  expect(forecast(18).word).toBe('Clear')
  expect(forecast(25).word).toBe('Cloudy')
  expect(forecast(67).word).toBe('Showers')
  expect(forecast(81).word).toBe('Storm')
  expect(forecast(90).word).toBe('Compact soon')
  expect(forecast(140).word).toBe('Compact soon')
})

test('a reading needs a window and derives percent when absent', () => {
  expect(toReading({ window: 0, tokens: 5 })).toBeNull()
  expect(toReading({ window: 200_000, tokens: 50_000 })).toEqual({ tokens: 50_000, window: 200_000, percent: 25 })
  expect(toReading({ window: 200_000, tokens: 1, percent: 7 })?.percent).toBe(7)
})

test('history skips repeats and keeps the last HISTORY readings', () => {
  const r = (tokens: number) => ({ tokens, window: 100, percent: tokens })
  let h = push([], r(1))
  h = push(h, r(1))
  expect(h.length).toBe(1)
  for (let i = 2; i <= HISTORY + 5; i++) h = push(h, r(i))
  expect(h.length).toBe(HISTORY)
  expect(h[h.length - 1]?.tokens).toBe(HISTORY + 5)
  expect(added(h)).toBe(1)
  expect(added([r(3)])).toBeNull()
})

test('spark and short render compactly', () => {
  const r = (tokens: number) => ({ tokens, window: 1_000_000, percent: Math.round(tokens / 10_000) })
  // One solid block per reading, its height that reading's share of the window in eighths.
  expect(spark([r(0), r(1_000_000)])).toBe('▁█')
  expect(spark([r(330_000), r(350_000), r(370_000), r(394_000)])).toBe('▃▃▃▄')
  // A flat history is flat at its own level.
  expect(spark([r(394_000), r(394_000)])).toBe('▄▄')
  // A new reading never redraws the earlier ones: each column keeps its height, so growth reads
  // as steps. Rescaling to the history's own range reshaped every column on every turn.
  const grown = [r(100_000), r(250_000), r(400_000), r(650_000), r(900_000)]
  for (let n = 1; n < grown.length; n++) {
    expect(spark(grown.slice(0, n + 1)).startsWith(spark(grown.slice(0, n)))).toBe(true)
  }
  expect(short(162_000)).toBe('162k')
  expect(short(1_000_000)).toBe('1M')
  expect(short(950)).toBe('950')
})

test('the band forecasts from a live reading on every surface', async ($, on) => {
  on('session.usage', () => ({
    value: { startedAt: 0, context: { tokens: 162_000, window: 200_000, percent: 81 }, rateLimits: [] },
  }))
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'token-weather',
      surface,
      component: 'AbovePrompt',
      props: BAND_PROPS,
      viewport: { columns: 100, rows: 30 },
    })
    expect((await ui.find({ type: 'Text', text: /Storm/ }))?.props.color).toBe('magenta')
    expect(await ui.find({ type: 'Text', text: /81% of context/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /162k \/ 200k/ })).toBeDefined()
    await ui.unmount()
  }
})

test('legend shares are whole percentages of the window', () => {
  expect(share(120_000, 200_000)).toBe('60%')
  expect(share(1_000, 200_000)).toBe('<1%')
  expect(share(0, 200_000)).toBe('0%')
  expect(share(5, 0)).toBe('0%')
})

test('a segment carries its percentage centred when it fits', () => {
  expect(segmentText(13, '60%')).toBe('     60%     ')
  expect(segmentText(12, '60%')).toBe('    60%     ')
  expect(segmentText(4, '60%')).toBe('    ')
  expect(segmentText(5, '60%')).toBe(' 60% ')
  expect(segmentText(0, '0%')).toBe('')
})

test('free space is what remains after used content and the buffer', () => {
  expect(freeTokens(200_000, 162_000, 0)).toBe(38_000)
  expect(freeTokens(200_000, 140_000, 45_000)).toBe(15_000)
  expect(freeTokens(200_000, 190_000, 45_000)).toBe(0)
})

test('free space reads as room before autocompact, shortening to fit', () => {
  expect(freeText(40, 38_000, 200_000).trim()).toBe('19% left before autocompact')
  expect(freeText(40, 38_000, 200_000)).toHaveLength(40)
  expect(freeText(12, 38_000, 200_000).trim()).toBe('19% left')
  expect(freeText(6, 38_000, 200_000)).toBe(' 19%  ')
  expect(freeText(3, 38_000, 200_000)).toBe('   ')
})

test('the autocompact buffer is named, never measured', () => {
  expect(bufferText(16).trim()).toBe('autocompact')
  expect(bufferText(16)).toHaveLength(16)
  // Too narrow for the name: blank, not a fixed percentage.
  expect(bufferText(9)).toBe('         ')
  expect(bufferText(0)).toBe('')
})

test('the bar width follows the band width', () => {
  expect(barWidth(120)).toBe(119)
  expect(barWidth(40)).toBe(39)
  expect(barWidth(0)).toBe(1)
})

test('the drawn bar fills the screen width at any size', async ($, on) => {
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: { tokens: 162_000, window: 200_000, percent: 81, breakdown: { categories: ROWS } as unknown as SessionContextBreakdown },
      rateLimits: [],
    },
  }))
  on('session.start', ($, e) => e)
  await $.session.start({ cwd: '/tmp', surface: 'terminal', isInteractive: true })
  for (const columns of [50, 120, 200]) {
    const ui = await $.ui.mount({
      plugin: 'token-weather',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { ...BAND_PROPS, bodyColumns: columns },
      viewport: { columns, rows: 30 },
    })
    const tree = (await ui.drawn()) as { children: { children?: unknown[] }[] }
    const barRow = tree.children[1] as { children: { children: string[] }[] }
    const cells = barRow.children.map(t => t.children.join('')).join('')
    expect(cells.length).toBe(columns - 1)
    await ui.unmount()
  }
})

test('the spark sits on the last row, never directly above the bar', async ($, on) => {
  // Block glyphs fill to the bottom of their cell, so on the row above the bar they fuse with
  // its filled cells into one stretched slab. On the legend row nothing is drawn beneath them.
  let tokens = 10_000
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: { tokens, window: 200_000, percent: Math.round(tokens / 2_000), breakdown: { categories: ROWS } as unknown as SessionContextBreakdown },
      rateLimits: [],
    },
  }))
  on('session.start', ($, e) => e)
  on('session.measure', () => ({ changed: [] }))
  await $.session.start({ cwd: '/tmp', surface: 'terminal', isInteractive: true })
  tokens = 190_000
  await $.session.measure({ context: { tokens, window: 200_000 }, rateLimits: [] } as never)
  const ui = await $.ui.mount({
    plugin: 'token-weather',
    surface: 'terminal',
    component: 'AbovePrompt',
    props: BAND_PROPS,
    viewport: { columns: 100, rows: 30 },
  })
  const text = (node: unknown): string =>
    typeof node === 'string' ? node : ((node as { children?: unknown[] }).children ?? []).map(text).join('')
  const tree = (await ui.drawn()) as { children: unknown[] }
  const rows = tree.children.map(text)
  expect(rows.length).toBe(3)
  expect(rows[0]).not.toMatch(/[▁▂▃▄▅▆▇█]/)
  expect(rows[2]).toMatch(/▁█/)
  await ui.unmount()
})

test('after a measurement the band draws each element in its /context colour', async ($, on) => {
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: {
        tokens: 162_000,
        window: 200_000,
        percent: 81,
        // A partial stub: the mod reads only `categories`.
        breakdown: { categories: ROWS } as unknown as SessionContextBreakdown,
      },
      rateLimits: [],
    },
  }))
  // The plugin samples on session.start; the test's hooks stand for the engine.
  on('session.start', ($, e) => e)
  await $.session.start({ cwd: '/tmp', surface: 'terminal', isInteractive: true })
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'token-weather',
      surface,
      component: 'AbovePrompt',
      props: BAND_PROPS,
      viewport: { columns: 100, rows: 30 },
    })
    const messages = await ui.find({ type: 'Text', text: /■ Messages 120k/ })
    expect(messages?.props.color).toBe('permission')
    expect((await ui.find({ type: 'Text', text: /■ MCP tools 30k/ }))?.props.color).toBe('inactive')
    expect((await ui.find({ type: 'Text', text: /■ System prompt 12k/ }))?.props.color).toBe('promptBorder')
    // The bar's segments carry the percentages, each in its element's /context colour.
    const messages60 = await ui.find({ type: 'Text', text: /^ +60% +$/ })
    expect(messages60?.props).toMatchObject({ color: 'permission', inverse: true })
    expect((await ui.find({ type: 'Text', text: /^ +15% +$/ }))?.props).toMatchObject({ color: 'inactive', inverse: true })
    expect(await ui.find({ type: 'Text', text: /█/ })).toBeUndefined()
    // 162k used + 45k buffer overfill a 200k window: no free cells, so no free label.
    expect(await ui.find({ type: 'Text', text: /free/ })).toBeUndefined()
    expect((await ui.find({ type: 'Text', text: /^ +autocompact +$/ }))?.props).toMatchObject({ color: 'inactive', inverse: true })
    expect(await ui.find({ type: 'Text', text: /23%/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /Autocompact/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /■ Messages 120k \(/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /Free space/ })).toBeUndefined()
    await ui.unmount()
  }
})

test('free space is a background track so it never blends with a grey element or the buffer', async ($, on) => {
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: { tokens: 162_000, window: 1_000_000, percent: 16, breakdown: { categories: ROWS } as unknown as SessionContextBreakdown },
      rateLimits: [],
    },
  }))
  on('session.start', ($, e) => e)
  await $.session.start({ cwd: '/tmp', surface: 'terminal', isInteractive: true })
  const ui = await $.ui.mount({
    plugin: 'token-weather',
    surface: 'terminal',
    component: 'AbovePrompt',
    props: { ...BAND_PROPS, bodyColumns: 120 },
    viewport: { columns: 120, rows: 30 },
  })
  const free = await ui.find({ type: 'Text', text: /left before autocompact/ })
  // One unbroken background track: no inverse grey fill, no pattern for the label to cut.
  expect(free?.props.backgroundColor).toBe('userMessageBackground')
  expect(free?.props.inverse).toBeFalsy()
  expect(free?.children.join('')).toMatch(/^ +\d+% left before autocompact +$/)
  // The coloured elements and the buffer stay filled.
  expect((await ui.find({ type: 'Text', text: /^ +12% +$/ }))?.props).toMatchObject({ color: 'permission', inverse: true })
  await ui.unmount()
})
