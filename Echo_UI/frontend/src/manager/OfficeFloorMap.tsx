import clsx from "clsx";
import { Check, Lock, Users } from "lucide-react";
import type { MeetingRoom } from "./actionTypes";

// Room positions in mockActionData use a 100 × 96 grid; the plan keeps that shape.
const W = 100;
const H = 96;
const pct = (value: number, of: number) => `${(100 * value) / of}%`;

/** A fictional office plan: each room is a button placed from its grid position and kept inside its floor. */
export default function OfficeFloorMap({
  rooms,
  selectedId,
  availableIds,
  onSelect,
}: {
  rooms: MeetingRoom[];
  selectedId: string | null;
  availableIds: Set<string>;
  onSelect: (id: string) => void;
}) {
  return (
    <div>
      <div
        className="@container relative w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100/70 dark:border-slate-700 dark:bg-slate-950"
        style={{ aspectRatio: `${W} / ${H}` }}
        aria-label="Fictional office floor plan. The room list offers the same choices."
      >
        {/* The two floors */}
        <div className="absolute inset-x-[3%] top-[4%] h-[46%] rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        <div className="absolute inset-x-[3%] top-[53%] h-[43%] rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        <span className="absolute left-[7%] top-[6%] text-[10px] font-semibold uppercase tracking-wider text-slate-400">North · Floor 2</span>
        <span className="absolute left-[7%] top-[55%] text-[10px] font-semibold uppercase tracking-wider text-slate-400">South · Floor 3</span>

        {rooms.map((room) => {
          const available = availableIds.has(room.id);
          const selected = selectedId === room.id;
          const small = room.width < 20;
          // "Collaboration Room A" shows as a big "A" with "Collaboration" under it, so nothing splits mid-word.
          const [kind, letter = ""] = room.name.split(" Room ");
          const floorBottom = room.y < 50 ? 46 : 91;
          const top = room.y + 1;
          const height = Math.min(room.height, floorBottom - top);
          return (
            <button
              key={room.id}
              type="button"
              disabled={!available}
              onClick={() => onSelect(room.id)}
              aria-pressed={selected}
              aria-label={`${room.name}, ${room.capacity} people, ${available ? "available" : "unavailable"}`}
              className={clsx(
                "absolute flex flex-col overflow-hidden rounded-lg border-2 p-[1.6%] text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500",
                selected
                  ? "border-indigo-500 bg-indigo-50 shadow-md ring-4 ring-indigo-500/15 dark:bg-indigo-500/15"
                  : available
                    ? "border-emerald-300 bg-emerald-50 hover:-translate-y-0.5 hover:border-emerald-400 hover:shadow-sm dark:border-emerald-500/40 dark:bg-emerald-500/10"
                    : "cursor-not-allowed border-dashed border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/40",
              )}
              style={{ left: pct(room.x, W), top: pct(top, H), width: pct(room.width, W), height: pct(height, H) }}
            >
              <span className="flex items-start justify-between gap-1">
                <span
                  className={clsx(
                    "grid size-6 shrink-0 place-items-center rounded-md text-sm font-bold ring-1 @md:size-7 @md:text-base",
                    selected ? "bg-indigo-600 text-white ring-indigo-600" : available ? "bg-white text-emerald-800 ring-emerald-200 dark:bg-slate-900 dark:text-emerald-200 dark:ring-emerald-500/30" : "bg-white text-slate-400 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700",
                  )}
                >
                  {letter}
                </span>
                {selected ? (
                  <span className="grid size-4 shrink-0 place-items-center rounded-full bg-indigo-600 text-white sm:size-5">
                    <Check className="size-3" />
                  </span>
                ) : (
                  !available && <Lock className="size-3 shrink-0 text-slate-400 sm:size-3.5" />
                )}
              </span>
              <span className={clsx("mt-1 truncate text-[11px] font-medium @md:text-sm", available ? "text-slate-700 dark:text-slate-200" : "text-slate-400")}>{kind}</span>
              <span className="mt-auto flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-slate-500 @md:text-xs dark:text-slate-400">
                <span className="inline-flex items-center gap-1">
                  <Users className="size-3" /> {room.capacity}
                </span>
                {!small && (
                  <span className={clsx("inline-flex items-center gap-1", available && "text-emerald-700 dark:text-emerald-300")}>
                    <span className={clsx("size-1.5 rounded-full", available ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600")} />
                    {available ? "Free" : "Busy"}
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500" aria-label="Floor plan legend">
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm border-2 border-emerald-300 bg-emerald-50" /> Free
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm border-2 border-dashed border-slate-300 bg-slate-50 dark:bg-slate-700" /> Busy or too small
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm border-2 border-indigo-500 bg-indigo-50" /> Selected
        </span>
      </div>
    </div>
  );
}
