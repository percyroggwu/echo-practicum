import { CalendarPlus, Check, FileText, Mail } from 'lucide-react'
import { useState } from 'react'
import type { Partner } from '../lib/api'

export type PartnerAction = 'feedback' | 'meeting'

/** Opens the manager's own email app with a draft. Echo itself never sends anything. */
export function mailtoUrl(to: string, subject: string, body: string) {
  const crlf = body.replace(/\r?\n/g, '\r\n')
  return `mailto:${encodeURIComponent(to).replace('%40', '@')}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(crlf)}`
}

function icsText(text: string) {
  return text.replace(/\\/g, '\\\\').replace(/;/g, '\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n')
}

// Calendar files allow 75 characters a line; longer ones continue on a line starting with a space.
function fold(line: string) {
  const parts = []
  for (let i = 0; i < line.length; i += 70) parts.push((i ? ' ' : '') + line.slice(i, i + 70))
  return parts.join('\r\n')
}

function stamp(d: Date) {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}T${p(d.getHours())}${p(d.getMinutes())}00`
}

/** A calendar invite in the attendee's local time. */
export function inviteFile({ title, start, minutes, agenda, attendee, attendeeName }: { title: string; start: Date; minutes: number; agenda: string; attendee: string | null; attendeeName: string | null }) {
  const end = new Date(start.getTime() + minutes * 60000)
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Echo//Partner meeting//EN',
    'BEGIN:VEVENT',
    `UID:${start.getTime()}-${Math.random().toString(36).slice(2)}@echo.local`,
    `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15)}Z`,
    `DTSTART:${stamp(start)}`,
    `DTEND:${stamp(end)}`,
    `SUMMARY:${icsText(title)}`,
    `DESCRIPTION:${icsText(agenda)}`,
    ...(attendee ? [`ATTENDEE;CN=${icsText(attendeeName ?? attendee)}:mailto:${attendee}`] : []),
    'END:VEVENT',
    'END:VCALENDAR',
  ]
  return lines.map(fold).join('\r\n') + '\r\n'
}

function nextWeekdayMorning() {
  const d = new Date()
  do d.setDate(d.getDate() + 1)
  while (d.getDay() === 0 || d.getDay() === 6)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T10:00`
}

function feedbackDraft(partner: Partner, managerName: string) {
  const hello = partner.Contact_Name ? `Hi ${partner.Contact_Name.split(' ')[0]},` : 'Hi,'
  const lost = partner.Praise_Not_Passed_On
    ? `\n\nFeedback on ${partner.Praise_Not_Passed_On} of those pieces of work didn't reach me, so I couldn't recognize it.`
    : ''
  return `${hello}\n\nMy team did ${partner.Contributions} pieces of work for ${partner.Team} in this period.${lost}\n\nWhen your team gives feedback on my team's work, could you copy me? It helps me make sure the work gets recognized.\n\nThanks,\n${managerName}`
}

function meetingAgenda(partner: Partner) {
  return `Agenda\n1. What my team did for ${partner.Team}: ${partner.Contributions} pieces of work in this period, and how it landed\n2. How feedback can reach both managers\n3. Upcoming requests: agree dates and priorities up front`
}

export default function PartnerActionDialog({ action, partner, managerName, onClose }: { action: PartnerAction; partner: Partner; managerName: string; onClose: () => void }) {
  const [text, setText] = useState(() => (action === 'feedback' ? feedbackDraft(partner, managerName) : meetingAgenda(partner)))
  const [when, setWhen] = useState(nextWeekdayMorning)
  const [minutes, setMinutes] = useState(30)
  const [copied, setCopied] = useState(false)
  const [saved, setSaved] = useState(false)
  const contact = partner.Contact_Name ? `${partner.Contact_Name}${partner.Contact_Email ? ` (${partner.Contact_Email})` : ''}` : 'No contact on record; add one in your email app'
  const field = 'mt-3 w-full resize-y rounded-xl border border-slate-200 bg-white p-3 text-sm leading-relaxed outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950'

  const download = () => {
    const title = `${partner.Team} and my team: cross-team work`
    const file = inviteFile({ title, start: new Date(when), minutes, agenda: text, attendee: partner.Contact_Email, attendeeName: partner.Contact_Name })
    const url = URL.createObjectURL(new Blob([file], { type: 'text/calendar' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `meeting-${partner.Team.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.ics`
    link.click()
    URL.revokeObjectURL(url)
    setSaved(true)
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-slate-950/40" onClick={onClose} />
      <div className="slide-in relative w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl dark:bg-slate-900">
        <div className="flex items-center gap-2 text-base font-semibold">
          {action === 'feedback' ? <Mail className="size-4 text-indigo-500" /> : <CalendarPlus className="size-4 text-indigo-500" />}
          {action === 'feedback' ? `Ask ${partner.Team} to share feedback` : `Schedule a meeting with ${partner.Team}`}
        </div>
        <p className="mt-1 text-xs text-slate-500">
          {action === 'feedback' ? 'Edit it in your own words. Your email app opens, and you press send.' : 'Downloads a calendar invite. Open it in your calendar to check it and send it.'}
        </p>
        <p className="mt-3 text-sm"><span className="text-slate-500">{action === 'feedback' ? 'To: ' : 'Invite: '}</span>{contact}</p>
        {partner.Contact_Name && <p className="text-xs text-slate-500">The manager who asked your team for the most work. Change this if someone else is better.</p>}
        {action === 'meeting' && (
          <div className="mt-3 flex flex-wrap gap-3">
            <label className="text-xs font-medium text-slate-500">
              When
              <input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} className="mt-1 block rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" />
            </label>
            <label className="text-xs font-medium text-slate-500">
              Length
              <select value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} className="mt-1 block rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100">
                {[15, 30, 45, 60].map((m) => <option key={m} value={m}>{m} minutes</option>)}
              </select>
            </label>
          </div>
        )}
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={action === 'feedback' ? 9 : 6} aria-label={action === 'feedback' ? 'Draft email' : 'Meeting agenda'} className={field} />
        <div className="mt-3 flex flex-wrap justify-end gap-2">
          <button onClick={onClose} className="rounded-xl px-3.5 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
            Close
          </button>
          {action === 'feedback' ? (
            <>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(text)
                  setCopied(true)
                }}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3.5 py-2 text-sm font-medium hover:border-indigo-300 dark:border-slate-700"
              >
                {copied ? <Check className="size-4" /> : <FileText className="size-4" />} {copied ? 'Copied' : 'Copy'}
              </button>
              <a href={mailtoUrl(partner.Contact_Email ?? '', `Sharing feedback on my team's work for ${partner.Team}`, text)} className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-500">
                <Mail className="size-4" /> Open in email
              </a>
            </>
          ) : (
            <button disabled={!when || Number.isNaN(new Date(when).getTime())} onClick={download} className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50">
              {saved ? <Check className="size-4" /> : <CalendarPlus className="size-4" />} {saved ? 'Downloaded' : 'Download invite'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
