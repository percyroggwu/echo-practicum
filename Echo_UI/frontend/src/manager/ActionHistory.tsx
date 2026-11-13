import clsx from "clsx";
import {
  Ban,
  Building2,
  CalendarCheck,
  CheckCircle2,
  Clock,
  RotateCcw,
  Utensils,
} from "lucide-react";
import { Badge, Button, Empty } from "../components/ui";
import { VENUES } from "./mockActionData";
import { formatDate, formatTime } from "./schedulingUtils";
import type { ActionStatus, EchoAction } from "./actionTypes";

const TONES: Record<
  ActionStatus,
  "slate" | "amber" | "blue" | "red" | "green"
> = {
  Draft: "slate",
  Planned: "amber",
  "Confirmed in prototype": "blue",
  Cancelled: "red",
  Completed: "green",
};

export default function ActionHistory({
  actions,
  onStatus,
}: {
  actions: EchoAction[];
  onStatus: (id: string, status: ActionStatus) => void;
}) {
  if (!actions.length)
    return (
      <Empty icon={CalendarCheck} title="No saved actions yet">
        Meetings, room plans, and team events saved in this prototype will
        appear here and survive a browser refresh.
      </Empty>
    );
  return (
    <div className="space-y-3">
      {actions.map((action) => {
        const venue =
          action.kind === "event"
            ? VENUES.find((item) => item.id === action.venueId)
            : null;
        return (
          <article
            key={action.id}
            className={clsx(
              "rounded-2xl border bg-white p-4 shadow-sm dark:bg-slate-900",
              action.status === "Cancelled"
                ? "border-slate-200 opacity-70 dark:border-slate-800"
                : "border-slate-200 dark:border-slate-800",
            )}
          >
            <div className="flex flex-wrap items-start gap-3">
              <span
                className={clsx(
                  "grid size-10 shrink-0 place-items-center rounded-xl",
                  action.kind === "meeting"
                    ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300"
                    : "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-300",
                )}
              >
                {action.kind === "meeting" ? (
                  <CalendarCheck className="size-5" />
                ) : (
                  <Utensils className="size-5" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h4 className="font-semibold">{action.title}</h4>
                  <Badge tone={TONES[action.status]}>{action.status}</Badge>
                </div>
                <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="size-3.5" />{" "}
                    {formatDate(action.slot.date)} ·{" "}
                    {formatTime(action.slot.start)}–
                    {formatTime(action.slot.end)}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Building2 className="size-3.5" />
                    {action.kind === "meeting"
                      ? action.location.label
                      : (venue?.name ?? "Venue")}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {action.origin.label} · Stored in this browser for the
                  selected demo manager
                </p>
              </div>
              <div className="flex gap-1">
                {action.status !== "Cancelled" &&
                  action.status !== "Completed" && (
                    <>
                      <Button
                        variant="ghost"
                        icon={CheckCircle2}
                        onClick={() => onStatus(action.id, "Completed")}
                      >
                        Complete
                      </Button>
                      <Button
                        variant="ghost"
                        icon={Ban}
                        onClick={() => onStatus(action.id, "Cancelled")}
                      >
                        Cancel
                      </Button>
                    </>
                  )}
                {action.status === "Cancelled" && (
                  <Button
                    variant="ghost"
                    icon={RotateCcw}
                    onClick={() => onStatus(action.id, "Planned")}
                  >
                    Restore as planned
                  </Button>
                )}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
