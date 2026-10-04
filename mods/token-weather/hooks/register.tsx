// Token Weather: a live forecast of the context window, above the prompt,
// with a bar and legend showing which elements fill it, in /context's colours.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { added, barCells, barWidth, forecast, freeTokens, isBuffer, push, bufferText, freeText, segmentText, share, short, spark, toReading, toSegments } from './weather'

// Held by the host, so the history survives a hot reload of this file.
// A theme key, so the track follows dark and light themes; it is no element's /context colour.
const FREE_TRACK = 'userMessageBackground'

const readings = atom({ plugin: 'token-weather', key: 'readings' } as const, [])
const segments = atom({ plugin: 'token-weather', key: 'segments' } as const, [])

// One measurement: the window's fill plus /context's breakdown by element.
async function sample($: EngineInterface) {
  const { context } = await $.session.usage({ breakdown: 'summary' })
  const r = toReading(context)
  if (r) await update($, readings, h => push(h, r))
  const rows = context.breakdown?.categories
  if (rows) await update($, segments, () => toSegments(rows))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    await sample($)
    return result
  })

  // Pushed after each main-thread turn, so subagent turns never land here.
  on('session.measure', async ($, e, next) => {
    const result = await next(e)
    await sample($)
    return result
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)

    let history = await read($, readings)
    if (history.length === 0) {
      // Nothing stored yet (first render after a reload): draw from a live reading.
      const r = toReading((await $.session.usage()).context)
      if (!r) return next(e)
      history = [r]
    }

    const now = history[history.length - 1]!
    const f = forecast(now.percent)
    const columns = e.props.bodyColumns
    const wide = columns >= 60
    const grew = added(history)
    const { Box, Text } = $.ui.resolve(e)

    const forecastRow = [
      <Text color={f.color} bold>{`${f.icon}  ${f.word}`}</Text>,
      <Text>{`  ${now.percent}% of context`}</Text>,
      <Text dimColor>{`  ${short(now.tokens)} / ${short(now.window)}`}</Text>,
    ]
    if (wide && grew !== null && grew > 0) {
      forecastRow.push(<Text dimColor>{`  +${short(grew)} last turn`}</Text>)
    }

    const stored = await read($, segments)
    const parts = stored.filter(s => !isBuffer(s))
    const reserve = stored.filter(isBuffer)
    // The trend: block glyphs, so never on the row directly above the bar (see LEVELS).
    const trend = wide ? <Text dimColor>{`  ${spark(history)}`}</Text> : null
    if (parts.length === 0) return <Box>{trend ? [...forecastRow, trend] : forecastRow}</Box>

    // The bar spans the band's width (one cell short, so it never wraps), laid
    // out as /context lays it out: each element's share of the window in its
    // colour, then free space, then the autocompact buffer at the far end.
    // Each segment carries its percentage where it fits.
    const width = barWidth(columns)
    const cells = barCells([...parts, ...reserve], now.window, width)
    const filled = cells.reduce((a, b) => a + b, 0)
    const reserveTokens = reserve.reduce((a, s) => a + s.tokens, 0)
    const free = freeTokens(now.window, now.tokens, reserveTokens)
    const bar = [
      ...parts.map((p, i) => (
        // inverse: the element's /context colour fills the cells and the label takes
        // the terminal's own background colour, which contrasts in dark and light themes.
        <Text color={p.color} inverse bold>
          {segmentText(cells[i] ?? 0, share(p.tokens, now.window))}
        </Text>
      )),
      // Free space: an unbroken track in the theme's user-message background, the room left
      // before autocompact written into it as the elements' percentages are. A dim inverse fill
      // drew the same grey as grey elements (System tools) and the buffer; a pattern or no fill
      // left the label cutting the line.
      <Text backgroundColor={FREE_TRACK}>{freeText(Math.max(0, width - filled), free, now.window)}</Text>,
      ...reserve.map((b, i) => (
        <Text color={b.color} inverse>
          {bufferText(cells[parts.length + i] ?? 0)}
        </Text>
      )),
    ]

    // The legend: largest elements first; fewer of them on a narrow band.
    const shown = wide ? parts : parts.slice(0, 3)
    const legend = shown.map(p => (
      <Text color={p.color}>{`■ ${p.name} ${short(p.tokens)}  `}</Text>
    ))
    if (trend) legend.push(trend)

    return (
      <Box flexDirection="column">
        <Box>{forecastRow}</Box>
        <Box>{bar}</Box>
        <Box flexWrap="wrap">{legend}</Box>
      </Box>
    )
  })
}
