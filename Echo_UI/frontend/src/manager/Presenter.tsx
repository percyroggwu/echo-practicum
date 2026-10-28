import clsx from 'clsx'
import { AlertTriangle, ChevronLeft, ChevronRight, Printer, ShieldCheck, X } from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { EvidenceChart } from '../components/run/Charts'
import { isSql, type Artifact, type Manager, type RunMeta, type SqlEvidence } from '../lib/api'

type Slide = { key: string; render: (print: boolean) => ReactNode }

const strip = (text: string) => text.replace(/\s*\[[A-Za-z]+\d*(?::[A-Za-z0-9_-]+)?\]/g, '').trim()

const TONE_TEXT = {
  good: 'text-emerald-500',
  fair: 'text-amber-500',
  poor: 'text-rose-500',
  neutral: '',
}

/** Turn a brief into presentation slides: one idea per slide, big type. */
function buildSlides(meta: RunMeta, artifact: Artifact, manager: Manager, period: string): Slide[] {
  const slides: Slide[] = []
  const meeting = meta.question.toLowerCase().startsWith('prepare me')
  const sources = new Map<string, SqlEvidence>()
  for (const e of [...(artifact.evidence ?? []), ...(artifact.delegations ?? []).flatMap((d) => d.evidence ?? [])]) if (isSql(e)) sources.set(e.citation_id, e)
  const chart = artifact.visualization?.charts?.[0]
  const chartSource = chart ? sources.get(chart.source_id) : undefined
  const muted = (print: boolean) => (print ? 'text-slate-500' : 'text-slate-400')

  slides.push({
    key: 'title',
    render: (print) => (
      <div className="flex h-full flex-col justify-center">
        <div className={clsx('text-sm font-semibold uppercase tracking-[0.2em]', print ? 'text-indigo-600' : 'text-indigo-300')}>{meeting ? 'Meeting brief' : 'Echo brief'}</div>
        <h1 className="mt-4 text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">{artifact.state_of_team ? 'State of the Team' : meta.question.replace(/^Prepare me for /i, '').replace(/^./, (c) => c.toUpperCase())}</h1>
        <p className={clsx('mt-6 text-lg', muted(print))}>
          {manager.Manager_Name} · {manager.Primary_Team} · {period}
        </p>
      </div>
    ),
  })

  if (artifact.metrics?.length)
    slides.push({
      key: 'metrics',
      render: (print) => (
        <div className="flex h-full flex-col justify-center">
          <h2 className="text-3xl font-semibold tracking-tight">At a glance</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {artifact.metrics!.map((m) => (
              <div key={m.label} className={clsx('rounded-2xl p-5', print ? 'border border-slate-200' : 'bg-white/5')}>
                <div className={clsx('text-5xl font-semibold tracking-tight', TONE_TEXT[m.tone])}>{m.value}</div>
                <div className={clsx('mt-2 text-sm', muted(print))}>{m.label}</div>
                {m.change && <div className={clsx('mt-1 text-sm font-medium', TONE_TEXT[m.tone] || muted(print))}>{m.change} since last time</div>}
              </div>
            ))}
          </div>
        </div>
      ),
    })

  if (artifact.state_of_team) {
    const sott = artifact.state_of_team
    sott.steps.forEach((step, i) =>
      slides.push({
        key: `sott-${i}`,
        render: (print) => (
          <div className="flex h-full flex-col justify-center">
            <div className={clsx('text-sm font-semibold uppercase tracking-[0.2em]', print ? 'text-indigo-600' : 'text-indigo-300')}>State of the Team · step {i + 1} of 4</div>
            <h2 className="mt-3 text-4xl font-semibold tracking-tight">{step.title}</h2>
            <p className={clsx('mt-3 text-lg', muted(print))}>{step.summary}</p>
            {step.items && (
              <ul className="mt-6 space-y-3 text-2xl">
                {step.items.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            )}
            {step.strengths && (
              <div className="mt-6 grid gap-6 sm:grid-cols-2">
                {(
                  [
                    ['Strengths to keep', step.strengths, 'text-emerald-500'],
                    ['Opportunities', step.opportunities ?? [], 'text-rose-500'],
                  ] as const
                ).map(([title, topics, tone]) => (
                  <div key={title}>
                    <div className={clsx('text-sm font-semibold uppercase tracking-wider', tone)}>{title}</div>
                    <ul className="mt-3 space-y-3">
                      {topics.map((t) => (
                        <li key={t.topic} className={clsx('rounded-2xl p-4', print ? 'border border-slate-200' : 'bg-white/5')}>
                          <div className="text-2xl font-semibold">
                            {t.topic} <span className={clsx('text-lg font-normal', muted(print))}>{t.favorable.toFixed(0)}% favorable</span>
                          </div>
                          <div className={clsx('text-sm', muted(print))}>
                            Gallup level: {t.level}
                            {t.change !== null ? ` · ${t.change >= 0 ? '+' : ''}${t.change.toFixed(0)} pts since last survey` : ''}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
            {step.questions && step.questions.length > 0 && (
              <div className="mt-6 grid gap-6 sm:grid-cols-2">
                <div>
                  <div className={clsx('text-sm font-semibold uppercase tracking-wider', muted(print))}>Ask the team</div>
                  <ul className="mt-3 space-y-3 text-xl">
                    {step.questions.map((q) => (
                      <li key={q}>“{q}”</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className={clsx('text-sm font-semibold uppercase tracking-wider', muted(print))}>Possible actions</div>
                  <ul className="mt-3 space-y-3 text-xl">
                    {(step.actions ?? []).map((a) => (
                      <li key={a}>☐ {a}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ),
      }),
    )
  }

  if (artifact.triangle) {
    const t = artifact.triangle
    slides.push({
      key: 'triangle',
      render: (print) => (
        <div className="flex h-full flex-col justify-center">
          <h2 className="flex items-center gap-3 text-3xl font-semibold tracking-tight">
            {t.agreement === 'conflict' && <AlertTriangle className="size-8 text-amber-500" />}
            {t.agreement === 'conflict' ? 'The evidence disagrees' : 'The evidence agrees'}
          </h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {(
              [
                ['The work', t.work],
                ['The feedback', t.feedback],
                ['The voice', t.voice],
              ] as const
            ).map(([title, side]) => (
              <div key={title} className={clsx('rounded-2xl p-5', print ? 'border border-slate-200' : 'bg-white/5')}>
                <div className={clsx('text-xs font-semibold uppercase tracking-wider', muted(print))}>{title}</div>
                <div className={clsx('mt-2 text-6xl font-semibold tracking-tight', TONE_TEXT[side.tone])}>{side.value}</div>
                <div className={clsx('mt-2 text-sm', muted(print))}>{side.label}</div>
              </div>
            ))}
          </div>
          <p className={clsx('mt-8 max-w-3xl text-lg leading-relaxed', print ? 'text-slate-700' : 'text-slate-300')}>{t.note}</p>
        </div>
      ),
    })
  }

  const found = artifact.findings?.length ? artifact.findings.map((f) => strip(f.text)) : strip(artifact.answer).split(/(?<=\.)\s+/).filter(Boolean)
  slides.push({
    key: 'found',
    render: () => (
      <div className="flex h-full flex-col justify-center">
        <h2 className="text-3xl font-semibold tracking-tight">What the newsroom found</h2>
        <ul className="mt-8 space-y-5">
          {found.map((line, i) => (
            <li key={i} className="flex gap-4 text-xl leading-relaxed sm:text-2xl">
              <span className="mt-3 size-2.5 shrink-0 rounded-full bg-indigo-400" />
              {line}
            </li>
          ))}
        </ul>
      </div>
    ),
  })

  if (chart && chartSource)
    slides.push({
      key: 'chart',
      render: (print) => (
        <div className="flex h-full flex-col justify-center">
          <h2 className="text-3xl font-semibold tracking-tight">{chart.title}</h2>
          <div className={clsx('mt-6 rounded-2xl p-4', print ? 'border border-slate-200' : 'bg-white/5')}>
            <EvidenceChart spec={chart} evidence={chartSource} height={380} />
          </div>
        </div>
      ),
    })

  if (artifact.next_steps?.length)
    slides.push({
      key: 'steps',
      render: () => (
        <div className="flex h-full flex-col justify-center">
          <h2 className="text-3xl font-semibold tracking-tight">{meeting ? 'Talking points' : 'What to do first'}</h2>
          <ol className="mt-8 space-y-5">
            {artifact.next_steps.map((step, i) => (
              <li key={i} className="flex gap-4 text-xl leading-relaxed sm:text-2xl">
                <span className="font-semibold text-indigo-400">{i + 1}</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      ),
    })

  if (artifact.examples?.length)
    slides.push({
      key: 'examples',
      render: (print) => (
        <div className="flex h-full flex-col justify-center">
          <h2 className="text-3xl font-semibold tracking-tight">Work worth recognizing</h2>
          <ul className="mt-8 space-y-4">
            {artifact.examples!.map((e) => (
              <li key={e.contribution_id} className={clsx('rounded-2xl p-5', print ? 'border border-slate-200' : 'bg-white/5')}>
                <div className="text-xl font-semibold">
                  {e.name} <span className={clsx('font-normal', muted(print))}>helped {e.team_helped}</span>
                </div>
                <div className={clsx('mt-1 text-base', print ? 'text-slate-600' : 'text-slate-300')}>{e.outcome}</div>
              </li>
            ))}
          </ul>
        </div>
      ),
    })

  slides.push({
    key: 'trust',
    render: (print) => (
      <div className="flex h-full flex-col justify-center">
        <h2 className="flex items-center gap-3 text-3xl font-semibold tracking-tight">
          <ShieldCheck className="size-8 text-emerald-500" /> How this was checked
        </h2>
        <ul className={clsx('mt-8 space-y-3 text-xl', print ? 'text-slate-700' : 'text-slate-300')}>
          <li>Every number comes from a cited query on {manager.Primary_Team}'s data only.</li>
          <li>ZeroSugar {artifact.verification?.decision === 'accept' ? 'verified' : 'reviewed'} the claims before you saw them.</li>
          <li>No individual survey responses are shown; groups under 5 are hidden.</li>
          <li>For human review and conversation, never for rating individuals.</li>
        </ul>
      </div>
    ),
  })
  return slides
}

/** Full-screen, swipeable deck for walking into a meeting; prints one slide per page. */
export default function Presenter({ meta, artifact, manager, period, onClose }: { meta: RunMeta; artifact: Artifact; manager: Manager; period: string; onClose: () => void }) {
  const slides = buildSlides(meta, artifact, manager, period)
  const [index, setIndex] = useState(0)
  const touch = useRef<number | null>(null)
  const go = (delta: number) => setIndex((i) => Math.max(0, Math.min(slides.length - 1, i + delta)))

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') go(1)
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') go(-1)
    }
    window.addEventListener('keydown', onKey)
    document.documentElement.classList.add('presenting')
    return () => {
      window.removeEventListener('keydown', onKey)
      document.documentElement.classList.remove('presenting')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <>
      <div
        className="presenter fixed inset-0 z-[60] flex flex-col bg-slate-950 text-white"
        onTouchStart={(e) => (touch.current = e.touches[0].clientX)}
        onTouchEnd={(e) => {
          if (touch.current === null) return
          const dx = e.changedTouches[0].clientX - touch.current
          if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1)
          touch.current = null
        }}
      >
        <div className="flex items-center gap-3 px-5 py-4 text-sm text-slate-400">
          <img src="/favicon.svg" alt="" className="size-6" />
          <span className="truncate">{manager.Primary_Team}</span>
          <span className="ml-auto tabular-nums">
            {index + 1} / {slides.length}
          </span>
          <button onClick={() => window.print()} className="rounded-lg p-2 hover:bg-white/10" aria-label="Print or save as PDF" title="Print or save as PDF">
            <Printer className="size-5" />
          </button>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-white/10" aria-label="Close presentation">
            <X className="size-5" />
          </button>
        </div>
        <div className="relative min-h-0 flex-1 overflow-y-auto px-6 pb-6 sm:px-16">
          <div key={slides[index].key} className="slide-in mx-auto h-full max-w-5xl">
            {slides[index].render(false)}
          </div>
        </div>
        <div className="flex items-center justify-between px-5 pb-5">
          <button onClick={() => go(-1)} disabled={index === 0} className="grid size-12 place-items-center rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-30" aria-label="Previous slide">
            <ChevronLeft className="size-6" />
          </button>
          <div className="flex gap-2">
            {slides.map((s, i) => (
              <button key={s.key} onClick={() => setIndex(i)} className={clsx('h-2 rounded-full transition-all', i === index ? 'w-8 bg-indigo-400' : 'w-2 bg-white/30')} aria-label={`Slide ${i + 1}`} />
            ))}
          </div>
          <button onClick={() => go(1)} disabled={index === slides.length - 1} className="grid size-12 place-items-center rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-30" aria-label="Next slide">
            <ChevronRight className="size-6" />
          </button>
        </div>
      </div>
      {/* Print copy: every slide on its own page, on white. */}
      <div className="print-deck hidden text-slate-900">
        {slides.map((s) => (
          <section key={s.key} className="print-slide px-12 py-10">
            {s.render(true)}
          </section>
        ))}
      </div>
    </>
  )
}
