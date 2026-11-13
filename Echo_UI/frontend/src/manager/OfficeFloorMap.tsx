import clsx from "clsx";
import type { MeetingRoom } from "./actionTypes";

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
      <svg
        viewBox="0 0 100 96"
        role="img"
        aria-labelledby="floor-title floor-desc"
        className="w-full rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950"
      >
        <title id="floor-title">Synthetic Echo office floor plan</title>
        <desc id="floor-desc">
          Clickable fictional meeting rooms. A directory below provides an
          accessible alternative.
        </desc>
        <rect
          x="3"
          y="5"
          width="94"
          height="86"
          rx="4"
          className="fill-white stroke-slate-300 dark:fill-slate-900 dark:stroke-slate-700"
        />
        <path
          d="M3 48h94M48 48v43"
          className="stroke-slate-200 dark:stroke-slate-700"
          strokeDasharray="2 2"
        />
        <text x="7" y="9" className="fill-slate-400 text-[3px] font-semibold">
          NORTH · FLOOR 2
        </text>
        <text x="7" y="55" className="fill-slate-400 text-[3px] font-semibold">
          SOUTH · FLOOR 3
        </text>
        <path
          d="M33 41h31M47 41v7M70 54h23"
          className="stroke-slate-300 dark:stroke-slate-600"
          strokeWidth="2"
        />
        {rooms.map((room) => {
          const available = availableIds.has(room.id);
          const selected = selectedId === room.id;
          return (
            <g
              key={room.id}
              role="button"
              tabIndex={0}
              aria-label={`${room.name}, capacity ${room.capacity}, ${available ? "available" : "unavailable"}`}
              aria-disabled={!available}
              onClick={() => available && onSelect(room.id)}
              onKeyDown={(event) =>
                available &&
                (event.key === "Enter" || event.key === " ") &&
                onSelect(room.id)
              }
              className={clsx(
                available ? "cursor-pointer" : "cursor-not-allowed opacity-55",
              )}
            >
              <rect
                x={room.x}
                y={room.y}
                width={room.width}
                height={room.height}
                rx="2"
                className={clsx(
                  "stroke-2 transition",
                  selected
                    ? "fill-indigo-600 stroke-indigo-700 dark:stroke-indigo-300"
                    : available
                      ? "fill-emerald-100 stroke-emerald-400 hover:fill-emerald-200 dark:fill-emerald-500/20 dark:stroke-emerald-500"
                      : "fill-slate-200 stroke-slate-300 dark:fill-slate-800 dark:stroke-slate-700",
                )}
              />
              <text
                x={room.x + 2}
                y={room.y + 6}
                className={clsx(
                  "pointer-events-none text-[3.1px] font-semibold",
                  selected
                    ? "fill-white"
                    : "fill-slate-700 dark:fill-slate-200",
                )}
              >
                {room.name.replace(" Room ", " ")}
              </text>
              <text
                x={room.x + 2}
                y={room.y + 11}
                className={clsx(
                  "pointer-events-none text-[2.7px]",
                  selected
                    ? "fill-indigo-100"
                    : "fill-slate-500 dark:fill-slate-400",
                )}
              >
                {room.capacity} people ·{" "}
                {available ? "Available" : "Unavailable"}
              </text>
            </g>
          );
        })}
        <rect
          x="48"
          y="84"
          width="22"
          height="7"
          rx="1"
          className="fill-slate-200 dark:fill-slate-800"
        />
        <text x="51" y="88.5" className="fill-slate-500 text-[2.8px]">
          COMMON AREA
        </text>
      </svg>
      <div
        className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500"
        aria-label="Floor plan legend"
      >
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm bg-emerald-200 ring-1 ring-emerald-400" />{" "}
          Available
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm bg-slate-200 ring-1 ring-slate-300 dark:bg-slate-700" />{" "}
          Unavailable or incompatible
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm bg-indigo-600" /> Selected
        </span>
      </div>
    </div>
  );
}
