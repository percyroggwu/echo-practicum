import clsx from 'clsx'
import { ArrowLeft, ChevronLeft, ChevronRight, Download, Expand, Loader2, Printer } from 'lucide-react'
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import { EvidenceChart } from '../components/run/Charts'
import { SERIES_COLORS } from '../lib/agents'
import { api, isSql, type Artifact, type Manager, type RunMeta, type SqlEvidence } from '../lib/api'
import { loadConversations, loadManagerCode, type Conversation } from './store'

// An investigation as a 16:9 deck, opened in its own tab from the manager view. The slides follow the same plan as
// the PowerPoint download (/api/presentation.pptx): cover, agenda, per question a result slide and a "so what" slide,
// actions for the quarter, and how it was checked. Content comes only from the runs' manager projections.

const W = 1280
const H = 720
const INK = '#1E2630'
const MUTED = '#556477'
const FAINT = '#6F8095'
const SAGE = '#63703C'
const PALE = '#C8D3A8'

const strip = (text?: string) => (text ?? '').replace(/\s*\[[A-Za-z]+\d*(?::[A-Za-z0-9_-]+)?\]/g, '').trim()
const tint = (colour: string, percent: number) => `color-mix(in srgb, ${colour} ${percent}%, white)`
const shade = (colour: string, percent: number) => `color-mix(in srgb, ${colour} ${percent}%, ${INK})`

type Result = { question: string; meta: RunMeta | null; artifact: Artifact | null }
type Slide = { kind: 'cover' | 'agenda' | 'actions' | 'close' } | { kind: 'result' | 'sowhat'; index: number }

const complete = (r: Result) => r.artifact?.status === 'complete'
const verified = (r: Result) => complete(r) && r.artifact!.verification?.decision === 'accept' && r.artifact!.verification?.status !== 'failed'

function plan(results: Result[]): Slide[] {
  const slides: Slide[] = [{ kind: 'cover' }]
  if (results.length > 1) slides.push({ kind: 'agenda' })
  results.forEach((r, index) => {
    slides.push({ kind: 'result', index })
    if (complete(r) && (r.artifact!.impact?.length || r.artifact!.next_steps?.length || r.artifact!.watch?.length)) slides.push({ kind: 'sowhat', index })
  })
  if (actions(results).length > 1) slides.push({ kind: 'actions' })
  slides.push({ kind: 'close' })
  return slides
}

function actions(results: Result[]) {
  return results.flatMap((r, index) => {
    const step = complete(r) ? strip(r.artifact!.next_steps?.[0]) : ''
    return step ? [{ step, question: r.question, index }] : []
  })
}

function chartOf(artifact: Artifact) {
  const spec = artifact.visualization?.charts?.[0]
  if (!spec) return null
  const evidence = [...(artifact.evidence ?? []), ...(artifact.delegations ?? []).flatMap((d) => d.evidence ?? [])]
  const source = evidence.find((e) => e.citation_id === spec.source_id && isSql(e)) as SqlEvidence | undefined
  return source?.rows.some((row) => row[spec.y] != null) ? { spec, source } : null
}

/* ---------------- slide pieces ---------------- */

function Ripples({ style }: { style: CSSProperties }) {
  return (
    <svg viewBox="0 0 600 600" className="pointer-events-none absolute" style={style} aria-hidden fill="none">
      {[60, 115, 175, 240, 310, 385].map((r, i) => (
        <circle key={r} cx="300" cy="300" r={r} stroke={PALE} strokeWidth={i === 0 ? 1.6 : 1} strokeOpacity={0.55 - i * 0.075} />
      ))}
    </svg>
  )
}

/** A light content slide: palette ribbon, eyebrow, title, and the footer with the page number. */
function Frame({ eyebrow, title, titleSize = 40, team, page, total, children }: { eyebrow: string; title?: string; titleSize?: number; team: string; page: number; total: number; children: ReactNode }) {
  return (
    <div className="relative h-full w-full overflow-hidden" style={{ background: '#FBFBF7', color: INK }}>
      <div className="echo-ribbon absolute inset-x-0 top-0 h-[7px]" />
      <div className="absolute left-16 top-10 text-[15px] font-semibold uppercase tracking-[0.12em]" style={{ color: SAGE }}>
        {eyebrow}
      </div>
      {title && (
        <h2 className="absolute left-16 right-16 top-[74px] font-display font-semibold leading-[1.15] tracking-tight" style={{ fontSize: titleSize }}>
          {title}
        </h2>
      )}
      {children}
      <div className="absolute bottom-7 left-16 text-[13px]" style={{ color: FAINT }}>
        Echo · {team}
      </div>
      <div className="absolute bottom-7 right-16 text-[13px] tabular-nums" style={{ color: FAINT }}>
        {page} / {total}
      </div>
    </div>
  )
}

function Dots({ items, dot, size = 19, numbered = false, color = INK }: { items: string[]; dot: string; size?: number; numbered?: boolean; color?: string }) {
  return (
    <ul className="space-y-3.5" style={{ fontSize: size, color, lineHeight: 1.4 }}>
      {items.map((item, i) => (
        <li key={i} className="flex gap-3.5">
          {numbered ? (
            <span className="mt-0.5 grid size-[30px] shrink-0 place-items-center rounded-full text-[15px] font-bold text-white" style={{ background: dot }}>
              {i + 1}
            </span>
          ) : (
            <span className="shrink-0 rounded-full" style={{ background: dot, width: 10, height: 10, marginTop: size * 0.5 }} />
          )}
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

function Dark({ children }: { children: ReactNode }) {
  return <div className="echo-entry-panel relative h-full w-full overflow-hidden text-white">{children}</div>
}

function Cover({ team, results, manager, period }: { team: string; results: Result[]; manager: Manager; period: string }) {
  const metaLine = [
    `Prepared for ${manager.Manager_Name}`,
    new Date().toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' }),
    period && `Data: ${period}`,
    `${results.length} question${results.length === 1 ? '' : 's'} investigated`,
  ].filter(Boolean)
  return (
    <Dark>
      <Ripples style={{ width: 1030, height: 1030, right: -400, top: -430 }} />
      <div className="absolute left-20 top-[72px] flex items-center gap-3 text-[19px]" style={{ color: PALE }}>
        <img src="/favicon.svg" alt="" className="size-9 rounded-lg ring-1 ring-white/20" /> Echo · team briefing
      </div>
      <div className="absolute bottom-[150px] left-20 right-40">
        <h1 className="font-display text-[76px] font-semibold leading-none tracking-tight">{team}</h1>
        <p className="mt-6 max-w-[880px] font-display text-[30px] leading-snug text-white/90">{strip(results[0]?.question)}</p>
      </div>
      <div className="absolute bottom-[70px] left-20 flex gap-10 text-[17px]" style={{ color: PALE }}>
        {metaLine.map((m) => (
          <span key={m}>{m}</span>
        ))}
      </div>
    </Dark>
  )
}

function Agenda({ results, team, page, total }: { results: Result[]; team: string; page: number; total: number }) {
  return (
    <Frame eyebrow="What we looked at" title={`${results.length} questions, one story`} titleSize={48} team={team} page={page} total={total}>
      <div className="absolute left-16 right-16 top-[192px] grid grid-cols-2 gap-x-7 gap-y-5">
        {results.slice(0, 8).map((r, i) => (
          <div key={i} className="flex h-[88px] items-center gap-5 rounded-2xl border bg-white px-5" style={{ borderColor: '#E3E8EE' }}>
            <span className="grid size-12 shrink-0 place-items-center rounded-full font-display text-[21px] font-semibold text-white" style={{ background: SERIES_COLORS[i % SERIES_COLORS.length] }}>
              {i + 1}
            </span>
            <span className="text-[21px] leading-snug">{r.question}</span>
          </div>
        ))}
      </div>
    </Frame>
  )
}

function ResultSlide({ result, index, count, team, page, total }: { result: Result; index: number; count: number; team: string; page: number; total: number }) {
  const colour = SERIES_COLORS[index % SERIES_COLORS.length]
  const eyebrow = count > 1 ? `Question ${index + 1} of ${count}` : 'The question'
  const title = result.question
  const titleSize = title.length < 70 ? 37 : 32
  const a = result.artifact
  if (!a || (a.status !== 'complete' && a.status !== 'declined'))
    return (
      <Frame eyebrow={eyebrow} title={title} titleSize={titleSize} team={team} page={page} total={total}>
        <p className="absolute left-16 top-[210px] text-[24px]" style={{ color: MUTED }}>
          This question did not finish, so it has no result to present.
        </p>
      </Frame>
    )
  if (a.status === 'declined')
    return (
      <Frame eyebrow={eyebrow} title={title} titleSize={titleSize} team={team} page={page} total={total}>
        <div className="absolute left-16 right-16 top-[210px] rounded-3xl border p-8" style={{ background: '#FFF1F2', borderColor: '#FECDD3' }}>
          <div className="text-[27px] font-bold" style={{ color: '#9F1239' }}>
            Echo declined this request
          </div>
          <p className="mt-4 text-[21px] leading-relaxed" style={{ color: '#3C4655' }}>
            {strip(a.answer)}
          </p>
        </div>
      </Frame>
    )
  const findings = (a.findings ?? []).filter((f) => (f.status ?? 'supported') === 'supported').map((f) => strip(f.text))
  const lead = findings[0] ?? strip(a.answer).split(/(?<=\.)\s/)[0]
  const chart = chartOf(a)
  // Beside a chart the column is narrow, so two supporting points fit; without one, three.
  const rest = findings.slice(1, chart ? 3 : 4)
  const leftW = chart ? 475 : W - 128
  return (
    <Frame eyebrow={eyebrow} title={title} titleSize={titleSize} team={team} page={page} total={total}>
      <div className="absolute left-16 top-[178px] flex flex-col" style={{ width: leftW, bottom: 64 }}>
        <div className="rounded-3xl px-7 py-6" style={{ background: tint(colour, 16) }}>
          <div className="text-[13px] font-bold uppercase tracking-[0.12em]" style={{ color: shade(colour, 70) }}>
            The headline
          </div>
          <p className="mt-2.5 font-display leading-snug" style={{ fontSize: lead.length < 150 ? 24 : 20 }}>
            {lead}
          </p>
        </div>
        {rest.length > 0 && (
          <div className="mt-6 min-h-0 flex-1 overflow-hidden">
            <Dots items={rest} dot={colour} size={chart ? 17 : 21} />
          </div>
        )}
        <div className={clsx('pt-3 text-[14px]', rest.length === 0 && 'mt-auto')} style={{ color: MUTED }}>
          {verified(result) ? "✓ Checked by ZeroSugar, Echo's fact-checker" : 'Not fully verified: read with care'}
        </div>
      </div>
      {chart && (
        <div className="absolute right-16 top-[178px] rounded-2xl border bg-white px-6 pb-3 pt-5" style={{ width: 645, bottom: 70, borderColor: '#E3E8EE', color: MUTED }}>
          <div className="text-[17px] font-semibold" style={{ color: INK }}>
            {chart.spec.title}
          </div>
          <div className="mt-3">
            <EvidenceChart spec={chart.spec} evidence={chart.source} height={370} />
          </div>
        </div>
      )}
    </Frame>
  )
}

function SoWhat({ result, index, count, team, page, total }: { result: Result; index: number; count: number; team: string; page: number; total: number }) {
  const a = result.artifact!
  const eyebrow = `${count > 1 ? `Question ${index + 1} of ${count}` : 'The question'} · so what`
  const impact = (a.impact ?? []).slice(0, 3).map(strip)
  const steps = (a.next_steps ?? []).slice(0, 3).map(strip)
  const watch = (a.watch ?? []).slice(0, 3)
  const caution = strip(a.limitations?.[0])
  const cards = [
    { heading: 'Why it matters', items: impact, fill: '#FFF8E8', line: '#F3DFA9', ink: '#92400E', dot: '#D9A24A', numbered: false },
    { heading: 'What to do first', items: steps, fill: '#F1F4E8', line: '#D6DCC4', ink: '#515C30', dot: '#7B934B', numbered: true },
  ].filter((c) => c.items.length)
  const long = cards.some((c) => c.items.join(' ').length > 380)
  return (
    <Frame eyebrow={eyebrow} title="What it means, and what to do" team={team} page={page} total={total}>
      <div className="absolute left-16 right-16 top-[163px] flex gap-7" style={{ bottom: watch.length || caution ? 240 : 80 }}>
        {cards.map((c) => (
          <div key={c.heading} className="min-w-0 flex-1 overflow-hidden rounded-3xl border px-7 py-6" style={{ background: c.fill, borderColor: c.line }}>
            <div className="text-[19px] font-bold" style={{ color: c.ink }}>
              {c.heading}
            </div>
            <div className="mt-4">
              <Dots items={c.items} dot={c.dot} size={long ? 17 : 19} numbered={c.numbered} />
            </div>
          </div>
        ))}
      </div>
      {(watch.length > 0 || caution) && (
        <div className="absolute bottom-[70px] left-16 right-16 flex h-[146px] gap-5">
          {watch.map((w) => (
            <div key={w.metric} className="min-w-0 max-w-[400px] flex-1 rounded-2xl border bg-white px-5 py-3.5" style={{ borderColor: '#E3E8EE' }}>
              <div className="text-[11px] font-bold uppercase tracking-[0.12em]" style={{ color: FAINT }}>
                Watch next quarter
              </div>
              <div className="mt-1.5 line-clamp-2 text-[16px] font-bold leading-snug">{w.metric}</div>
              <div className="mt-1 line-clamp-2 text-[14px] leading-snug" style={{ color: MUTED }}>
                now {w.baseline} · aim {w.goal}
              </div>
            </div>
          ))}
          {caution && (
            <p className={clsx('flex items-center text-[15px] leading-snug', watch.length ? 'ml-auto w-[330px] shrink-0' : 'flex-1')} style={{ color: FAINT }}>
              <span>
                <span className="font-semibold">Before you act:</span> {caution}
              </span>
            </p>
          )}
        </div>
      )}
    </Frame>
  )
}

function Actions({ results, team, page, total }: { results: Result[]; team: string; page: number; total: number }) {
  return (
    <Frame eyebrow="Putting it together" title="Actions for this quarter" titleSize={48} team={team} page={page} total={total}>
      <div className="absolute left-16 right-16 top-[187px] space-y-3.5">
        {actions(results)
          .slice(0, 5)
          .map((a, i) => (
            <div key={i} className="flex items-center gap-5 rounded-2xl border bg-white px-6 py-3.5" style={{ borderColor: '#E3E8EE' }}>
              <span className="grid size-12 shrink-0 place-items-center rounded-full font-display text-[21px] font-semibold text-white" style={{ background: SERIES_COLORS[a.index % SERIES_COLORS.length] }}>
                {i + 1}
              </span>
              <span className="min-w-0">
                <span className="line-clamp-2 leading-snug" style={{ fontSize: a.step.length > 95 ? 18 : 20 }}>
                  {a.step}
                </span>
                <span className="mt-0.5 block truncate text-[14px]" style={{ color: FAINT }}>
                  From: {a.question}
                </span>
              </span>
            </div>
          ))}
      </div>
    </Frame>
  )
}

function Close({ results, team, period }: { results: Result[]; team: string; period: string }) {
  const checked = results.filter(verified).length
  // Only the offline demo re-runs every query before release; live answers are checked against their cited sources.
  const rerun = results.every((r) => r.meta?.mode === 'offline')
  const facts = [
    `Only ${team}'s records and survey scores${period ? `, ${period}` : ''}.`,
    rerun ? 'Every number comes from a query that was re-run before release.' : 'Every number traces back to a cited database query.',
    'Team-level results only: no individual survey responses are shown.',
  ]
  return (
    <Dark>
      <Ripples style={{ width: 1030, height: 1030, left: -430, bottom: -430 }} />
      <div className="absolute left-[422px] right-16 top-[124px]">
        <div className="text-[17px] font-bold uppercase tracking-[0.12em]" style={{ color: PALE }}>
          How this was checked
        </div>
        <h2 className="mt-4 text-balance font-display text-[44px] font-semibold leading-tight">
          {checked} of {results.length} result{results.length === 1 ? '' : 's'} passed Echo's fact{'\u2011'}check
        </h2>
        <div className="mt-9">
          <Dots items={facts} dot={PALE} size={21} color="#E4E8E0" />
        </div>
        <p className="mt-10 text-[16px]" style={{ color: PALE }}>
          Echo supports human review. It is not for personnel decisions.
        </p>
      </div>
    </Dark>
  )
}

/* ---------------- the page ---------------- */

/** Scale a 1280×720 slide to fit the space it is given. */
function useFit(ref: React.RefObject<HTMLDivElement | null>) {
  const [scale, setScale] = useState(1)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const fit = () => setScale(Math.min(el.clientWidth / W, el.clientHeight / H))
    fit()
    const observer = new ResizeObserver(fit)
    observer.observe(el)
    return () => observer.disconnect()
  }, [ref])
  return scale
}

export default function Present() {
  const { id = '' } = useParams()
  const [state, setState] = useState<{ manager: Manager; conversation: Conversation; results: Result[] } | null>(null)
  const [error, setError] = useState('')
  const [page, setPage] = useState(0)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState('')
  const stage = useRef<HTMLDivElement>(null)
  const scale = useFit(stage)

  // The slides are designed on white; the deck ignores the app's dark mode.
  useEffect(() => {
    const root = document.documentElement
    const wasDark = root.classList.contains('dark')
    root.classList.remove('dark')
    return () => {
      if (wasDark) root.classList.add('dark')
    }
  }, [])

  useEffect(() => {
    const code = loadManagerCode()
    const conversation = code ? loadConversations(code).find((c) => c.id === id) : undefined
    if (!code || !conversation) {
      setError('This investigation is not saved in this browser. Open Echo, choose the investigation, and press Present again.')
      return
    }
    Promise.all([
      api.lookupManager(code),
      Promise.all(conversation.messages.map((m) => api.managerRun(m.runId).catch(() => null))),
    ])
      .then(([manager, runs]) => {
        const results = conversation.messages.map((m, i) => ({ question: m.question, meta: runs[i]?.meta ?? null, artifact: runs[i]?.artifact ?? null }))
        document.title = `Echo briefing · ${manager.Primary_Team}`
        setState({ manager, conversation, results })
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
  }, [id])

  const slides = state ? plan(state.results) : []
  const last = slides.length - 1
  const go = useCallback((next: number) => setPage(Math.max(0, Math.min(last, next))), [last])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (['ArrowRight', 'PageDown', ' '].includes(e.key)) go(page + 1)
      else if (['ArrowLeft', 'PageUp'].includes(e.key)) go(page - 1)
      else if (e.key === 'Home') go(0)
      else if (e.key === 'End') go(last)
      else if (e.key.toLowerCase() === 'f') document.documentElement.requestFullscreen?.().catch(() => undefined)
      else return
      e.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, page, last])

  async function downloadPptx() {
    if (!state) return
    setDownloading(true)
    setDownloadError('')
    try {
      const response = await fetch(api.presentationUrl(state.manager.Manager_ID, state.conversation.messages.map((m) => m.runId)))
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `The download failed (${response.status}).`)
      }
      const link = document.createElement('a')
      link.href = URL.createObjectURL(await response.blob())
      link.download = `Echo briefing - ${state.manager.Primary_Team}.pptx`
      link.click()
      URL.revokeObjectURL(link.href)
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : String(e))
    } finally {
      setDownloading(false)
    }
  }

  if (error)
    return (
      <div className="echo-entry-panel grid h-full place-items-center px-6 text-center text-white">
        <div className="max-w-md">
          <h1 className="font-display text-3xl font-semibold">Nothing to present</h1>
          <p className="mt-3 text-white/75">{error}</p>
        </div>
      </div>
    )
  if (!state)
    return (
      <div className="echo-entry-panel grid h-full place-items-center text-white/80">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )

  const { manager, results } = state
  const team = manager.Primary_Team
  const first = results.find((r) => r.meta)?.meta
  const period = first ? `${first.start_date} to ${first.end_date}` : ''
  const total = slides.length
  const render = (slide: Slide, i: number) => {
    const common = { team, page: i + 1, total }
    switch (slide.kind) {
      case 'cover':
        return <Cover team={team} results={results} manager={manager} period={period} />
      case 'agenda':
        return <Agenda results={results} {...common} />
      case 'actions':
        return <Actions results={results} {...common} />
      case 'close':
        return <Close results={results} team={team} period={period} />
      case 'result':
        return <ResultSlide result={results[slide.index]} index={slide.index} count={results.length} {...common} />
      case 'sowhat':
        return <SoWhat result={results[slide.index]} index={slide.index} count={results.length} {...common} />
    }
  }
  const chrome = 'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition'

  return (
    <div className="present-shell flex h-full flex-col bg-[#141a21] text-white">
      <header className="present-chrome flex flex-wrap items-center gap-2 border-b border-white/10 px-4 py-2.5">
        <button onClick={() => window.close()} className={clsx(chrome, 'text-white/70 hover:bg-white/10 hover:text-white')} title="Close this tab">
          <ArrowLeft className="size-3.5" /> Back to Echo
        </button>
        <div className="min-w-0 flex-1 truncate px-2 text-sm text-white/80">
          <span className="font-display font-semibold text-white">{team}</span> · {results.length} result{results.length === 1 ? '' : 's'}
        </div>
        {downloadError && <span className="max-w-md truncate text-xs text-rose-300" title={downloadError}>{downloadError}</span>}
        <button onClick={downloadPptx} disabled={downloading} className={clsx(chrome, 'text-white/80 hover:bg-white/10 hover:text-white disabled:opacity-50')}>
          {downloading ? <Loader2 className="size-3.5 animate-spin" /> : <Download className="size-3.5" />} Download PowerPoint
        </button>
        <button onClick={() => window.print()} className={clsx(chrome, 'text-white/80 hover:bg-white/10 hover:text-white')} title="Print, or choose Save as PDF">
          <Printer className="size-3.5" /> Save as PDF
        </button>
        <button onClick={() => document.documentElement.requestFullscreen?.().catch(() => undefined)} className={clsx(chrome, 'bg-[#a8b58a] text-[#20241a] hover:bg-[#bdc7a2]')} title="Full screen (F)">
          <Expand className="size-3.5" /> Present
        </button>
      </header>

      <div ref={stage} className="present-stage relative min-h-0 flex-1 p-6">
        <div className="present-fit absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ width: W * scale, height: H * scale }}>
          <div className="present-scale origin-top-left overflow-hidden rounded-md shadow-2xl shadow-black/40" style={{ width: W, transform: `scale(${scale})` }}>
            {slides.map((slide, i) => (
              <section key={i} className={clsx('present-page', i !== page && 'present-hidden')} style={{ width: W, height: H }} aria-hidden={i !== page}>
                {render(slide, i)}
              </section>
            ))}
          </div>
        </div>
      </div>

      <footer className="present-chrome flex items-center justify-center gap-4 px-4 pb-4">
        <button onClick={() => go(page - 1)} disabled={page === 0} className="grid size-9 place-items-center rounded-full bg-white/10 transition hover:bg-white/20 disabled:opacity-30" aria-label="Previous slide">
          <ChevronLeft className="size-5" />
        </button>
        <div className="flex items-center gap-1.5">
          {slides.map((_, i) => (
            <button key={i} onClick={() => go(i)} className={clsx('h-1.5 rounded-full transition-all', i === page ? 'w-6 bg-[#a8b58a]' : 'w-1.5 bg-white/30 hover:bg-white/50')} aria-label={`Slide ${i + 1}`} />
          ))}
        </div>
        <button onClick={() => go(page + 1)} disabled={page === last} className="grid size-9 place-items-center rounded-full bg-white/10 transition hover:bg-white/20 disabled:opacity-30" aria-label="Next slide">
          <ChevronRight className="size-5" />
        </button>
        <span className="w-14 text-right text-xs tabular-nums text-white/50">
          {page + 1} / {total}
        </span>
      </footer>
    </div>
  )
}
