import {
  ArrowRight,
  CalendarCheck,
  Info,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { Badge, Button } from "../components/ui";

export default function ActionRecommendationCard({
  recommendation,
  onOpen,
}: {
  recommendation: {
    category: string;
    title: string;
    context: string;
    limitation: string;
    action: string;
    tool: "scheduler" | "event";
  };
  onOpen: () => void;
}) {
  const existing = recommendation.category === "Existing Echo evidence";
  return (
    <article className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-3">
        <span className="grid size-10 place-items-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300">
          {existing ? (
            <Sparkles className="size-5" />
          ) : (
            <Info className="size-5" />
          )}
        </span>
        <Badge tone={existing ? "blue" : "slate"}>
          {recommendation.category}
        </Badge>
      </div>
      <h3 className="mt-4 text-lg font-semibold">{recommendation.title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {recommendation.context}
      </p>
      <div className="mt-3 flex gap-2 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">
        <TriangleAlert className="mt-0.5 size-4 shrink-0" />
        <span>
          <strong>Important uncertainty:</strong> {recommendation.limitation}
        </span>
      </div>
      <div className="mt-4 flex-1">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Suggested intervention
        </div>
        <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">
          {recommendation.action}
        </p>
      </div>
      <Button
        variant="primary"
        className="mt-5 w-full"
        icon={recommendation.tool === "scheduler" ? CalendarCheck : ArrowRight}
        onClick={onOpen}
      >
        {recommendation.tool === "scheduler"
          ? "Open scheduler"
          : "Plan optional event"}
      </Button>
    </article>
  );
}
