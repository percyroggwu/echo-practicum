import { ArrowRight, CalendarCheck, HeartHandshake, Info, Scale, Utensils } from "lucide-react";
import { Button } from "../components/ui";

const ICONS = { "recognition-gap": HeartHandshake, "workload-check": Scale, "team-connection": Utensils } as const;

/** One suggested next step: what Echo saw, the one thing to check first, and a button. */
export default function ActionRecommendationCard({
  recommendation,
  onOpen,
}: {
  recommendation: {
    id: string;
    category: string;
    title: string;
    context: string;
    limitation: string;
    action: string;
    tool: "scheduler" | "event";
  };
  onOpen: () => void;
}) {
  const Icon = ICONS[recommendation.id as keyof typeof ICONS] ?? CalendarCheck;
  return (
    <article className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300">
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <h3 className="font-semibold leading-tight">{recommendation.title}</h3>
          <div className="text-[11px] text-slate-400">{recommendation.category}</div>
        </div>
      </div>
      <p className="mt-3 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{recommendation.context}</p>
      <p className="mt-3 flex gap-1.5 text-xs leading-5 text-slate-500">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        {recommendation.limitation}
      </p>
      <Button
        variant="primary"
        className="mt-4 w-full"
        icon={recommendation.tool === "scheduler" ? CalendarCheck : ArrowRight}
        onClick={onOpen}
      >
        {recommendation.action}
      </Button>
    </article>
  );
}
