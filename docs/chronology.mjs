/* Explicit graph chronology. No prose parsing, cutoff-derived endpoints or lifespan inference. */
export const chronologyOf = node => node?.chronology?.version === 1 ? node.chronology : null;
export const dateBounds = date => date?.precision === 'year_range'
  ? [date.earliest, date.latest]
  : Number.isFinite(date?.year) ? [date.year, date.year + ({decade: 9, century: 99}[date.precision] || 0)] : null;
const yearText = year => year < 0 ? `${Math.abs(year)} BCE` : String(year);
export function dateText(date) {
  const b = dateBounds(date);
  if (!b) return 'date unestablished';
  let text = date.precision === 'day' ? `${yearText(date.year)}-${String(date.month).padStart(2, '0')}-${String(date.day).padStart(2, '0')}`
    : date.precision === 'month' ? `${yearText(date.year)}-${String(date.month).padStart(2, '0')}`
    : date.precision === 'decade' ? `${yearText(date.year)}s`
    : b[0] !== b[1] ? `${yearText(b[0])}–${yearText(b[1])}` : yearText(b[0]);
  if (date.qualifier) text += ` (${date.qualifier.replace(/_/g, ' ')})`;
  if (date.alternatives?.length) text += `; alternate citation: ${date.alternatives.map(a => yearText(a.year)).join(', ')}`;
  return text;
}
export const chronologyLabel = node => chronologyOf(node)?.label || node?.date_label || '';
export const chronologyEvents = node => (chronologyOf(node)?.events || [])
  .map(event => ({...event, bounds: dateBounds(event.date)})).filter(e => e.bounds)
  .sort((a, b) => a.bounds[0] - b.bounds[0] || a.bounds[1] - b.bounds[1] || a.label.localeCompare(b.label));
const extent = bounds => bounds.length ? {start: Math.min(...bounds.map(b => b[0])), end: Math.max(...bounds.map(b => b[1]))} : null;
export function contributionSpan(node) {
  const events = chronologyEvents(node);
  const selected = events.filter(e => e.track === 'contributions');
  return extent((selected.length ? selected : events).map(e => e.bounds));
}
export function chronologySpan(node) {
  const c = chronologyOf(node);
  if (!c) return null;
  const dates = chronologyEvents(node).map(e => e.bounds);
  for (const interval of c.intervals || []) {
    const a = dateBounds(interval.start), b = dateBounds(interval.end);
    if (a) dates.push(a);
    if (b) dates.push(b);
  }
  const e = extent(dates);
  return e ? {...e, endKind: 'selection', openStart: false, coverage: null,
    precision: 'explicit', curated: true, chronological: true, basis: c.selection_note,
    contributionSpan: contributionSpan(node)} : null;
}
export function chronologyGeometry(node, scale) {
  const selection = contributionSpan(node);
  return {
    selection: selection ? {x: scale(selection.start), w: scale(selection.end) - scale(selection.start)} : null,
    events: chronologyEvents(node).map(e => ({...e, x: scale((e.bounds[0] + e.bounds[1]) / 2),
      x0: scale(e.bounds[0]), x1: scale(e.bounds[1]), uncertain: e.bounds[0] !== e.bounds[1] || Boolean(e.date.qualifier)})),
    intervals: (chronologyOf(node)?.intervals || []).map(i => {
      const a = dateBounds(i.start), b = dateBounds(i.end);
      return {...i, x: scale(a[0]), w: b ? scale(b[1]) - scale(a[0]) : 0, unknownEnd: !b};
    }),
  };
}
