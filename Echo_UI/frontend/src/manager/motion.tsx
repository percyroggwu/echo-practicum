import clsx from 'clsx'
import { useEffect, useRef, useState } from 'react'

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** A number that eases from its previous value to the new one: up from 0 on first show, old to new when the period changes. */
export function CountUp({ value, ms = 700, format = (n: number) => Math.round(n).toLocaleString() }: { value: number; ms?: number; format?: (n: number) => string }) {
  const [shown, setShown] = useState(() => (reducedMotion() ? value : 0))
  const from = useRef(shown)
  useEffect(() => {
    if (reducedMotion()) {
      setShown(value)
      return
    }
    const start = performance.now()
    const begin = from.current
    let frame = 0
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms)
      const next = begin + (value - begin) * (1 - (1 - t) ** 3)
      from.current = next
      setShown(next)
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    // Background tabs pause animation frames; the final value still lands on time.
    const settle = window.setTimeout(() => {
      cancelAnimationFrame(frame)
      from.current = value
      setShown(value)
    }, ms + 100)
    return () => {
      cancelAnimationFrame(frame)
      window.clearTimeout(settle)
    }
  }, [value, ms])
  return <>{format(shown)}</>
}

/** Grey placeholder in the shape of the content that is loading. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse rounded-xl bg-slate-200/80 dark:bg-slate-800', className)} aria-hidden />
}
