import clsx from 'clsx'
import { ChevronDown } from 'lucide-react'
import { useState, type ReactNode } from 'react'

const CARD = 'rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900'

/** A section that can be minimized to its title line. */
export default function Fold({
  title,
  icon,
  meta,
  defaultOpen = true,
  className = CARD,
  children,
}: {
  title: ReactNode
  icon?: ReactNode
  meta?: ReactNode
  defaultOpen?: boolean
  className?: string
  children: ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <section className={className}>
      <button onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-center gap-2 px-5 py-3.5 text-left">
        {icon}
        <span className="text-sm font-semibold">{title}</span>
        <span className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          {meta}
          <ChevronDown className={clsx('size-4 shrink-0 text-slate-400 transition', open && 'rotate-180')} />
        </span>
      </button>
      {open && <div className="slide-in px-5 pb-5">{children}</div>}
    </section>
  )
}
