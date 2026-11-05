import { PageTitle } from '../components/Layout'
import { ErrorNote, Spinner } from '../components/ui'
import { api, type OrgOverview } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { VisibilityStack, visibilityGroups } from '../manager/TeamPulse'

const CARD = 'rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900'

function Tile({ value, label, note }: { value: string; label: string; note: string }) {
  return (
    <section className={CARD}>
      <div className="text-3xl font-semibold tabular-nums tracking-tight">{value}</div>
      <div className="mt-1 text-sm font-medium">{label}</div>
      <div className="mt-1 text-xs text-slate-500">{note}</div>
    </section>
  )
}

function pct(part: number, whole: number) {
  return whole ? Math.round((100 * part) / whole) : 0
}

function Overview({ data }: { data: OrgOverview }) {
  const t = data.totals
  const unnoticed = t.No_Praise + t.Praise_Not_Passed_On
  const fte = Math.round(t.Unnoticed_Hours / data.hours_per_fte)
  const cost = (t.Unnoticed_Hours * data.assumed_hourly_cost) / 1e6
  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile value={`${pct(t.Cross_Team_Hours, t.All_Hours)}%`} label="of hours cross team lines" note={`${Math.round(t.Cross_Team_Hours).toLocaleString()} of ${Math.round(t.All_Hours).toLocaleString()} hours`} />
        <Tile value={`${pct(unnoticed, t.Cross_Team)}%`} label="of that work went unnoticed" note={`${unnoticed.toLocaleString()} of ${t.Cross_Team.toLocaleString()} pieces of work`} />
        <Tile value={`~${fte}`} label="full-time people's worth" note={`${Math.round(t.Unnoticed_Hours).toLocaleString()} unnoticed hours, at ${data.hours_per_fte.toLocaleString()} hours a year`} />
        <Tile value={`~$${cost.toFixed(1)}M`} label="size of the blind spot" note={`Assumes $${data.assumed_hourly_cost} an hour. Not a saving.`} />
      </div>

      <section className={CARD}>
        <h2 className="text-sm font-semibold">How far cross-team work was seen, by department</h2>
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
          {visibilityGroups(t).map((g) => (
            <li key={g.label} className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
              <span className="size-2.5 rounded-sm" style={{ backgroundColor: g.color }} />
              {g.label} ({pct(g.value, t.Cross_Team)}%)
            </li>
          ))}
        </ul>
        <div className="mt-4 space-y-3">
          {data.departments.map((d) => (
            <div key={d.Department} className="grid items-center gap-x-3 gap-y-1 sm:grid-cols-[130px_minmax(0,1fr)_190px]">
              <div className="text-sm font-medium">{d.Department}</div>
              <VisibilityStack v={d} />
              <div className="text-xs tabular-nums text-slate-500 sm:text-right">
                {pct(d.No_Praise + d.Praise_Not_Passed_On, d.Cross_Team)}% unnoticed · {Math.round(d.Unnoticed_Hours).toLocaleString()} hours
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className={CARD}>
          <h2 className="text-sm font-semibold">Which departments depend on which</h2>
          <p className="mt-0.5 text-xs text-slate-500">Largest flows of hours from one department to another</p>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500">
                <th className="pb-1.5 font-medium">Helper</th>
                <th className="pb-1.5 font-medium">Helped</th>
                <th className="pb-1.5 text-right font-medium">Hours</th>
              </tr>
            </thead>
            <tbody>
              {data.dependencies.map((d) => (
                <tr key={`${d.Helper}-${d.Helped}`} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="py-1.5">{d.Helper}</td>
                  <td className="py-1.5">{d.Helped}</td>
                  <td className="py-1.5 text-right tabular-nums">{d.Hours.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className={CARD}>
          <h2 className="text-sm font-semibold">What a pilot would measure</h2>
          <p className="mt-0.5 text-xs text-slate-500">Starting points to compare against. Echo's value is unproven until these move on real data.</p>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500">
                <th className="pb-1.5 font-medium">Measure</th>
                <th className="pb-1.5 text-right font-medium">Now</th>
                <th className="pb-1.5 text-right font-medium">Aim</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1.5">Cross-team work unnoticed</td>
                <td className="py-1.5 text-right tabular-nums">{pct(unnoticed, t.Cross_Team)}%</td>
                <td className="py-1.5 text-right">Lower</td>
              </tr>
              <tr className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1.5">Cross-team work recognized</td>
                <td className="py-1.5 text-right tabular-nums">{pct(t.Recognized, t.Cross_Team)}%</td>
                <td className="py-1.5 text-right">Higher</td>
              </tr>
              <tr className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1.5">Requests from other teams finished late</td>
                <td className="py-1.5 text-right tabular-nums">{data.late.crossing ?? 'n/a'}%</td>
                <td className="py-1.5 text-right">Lower</td>
              </tr>
            </tbody>
          </table>
          <p className="mt-3 text-xs text-slate-500">
            Same-team requests finish late {data.late.inside ?? 'n/a'}% of the time in this synthetic data, so the size of that gap comes from how the data was generated.
          </p>
        </section>
      </div>
      <p className="text-xs text-slate-500">
        Department totals only, with no names. Based on formal records, so informal thanks may not be counted. A real rollout would limit this view to department and organization leaders.
      </p>
    </div>
  )
}

export default function AcrossTeams() {
  const overview = useAsync(api.orgOverview)
  return (
    <>
      <PageTitle title="Across teams" subtitle="Leadership view of work that crosses the org chart, over the last 12 months (Oct 2025 – Sep 2026). Synthetic data." />
      {overview.loading && !overview.data ? <Spinner /> : overview.error ? <ErrorNote error={overview.error} /> : <Overview data={overview.data!} />}
    </>
  )
}
