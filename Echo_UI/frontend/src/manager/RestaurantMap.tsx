import clsx from "clsx";
import { MapPin, Utensils } from "lucide-react";
import type { Venue } from "./actionTypes";

export default function RestaurantMap({
  venues,
  selectedId,
  onSelect,
}: {
  venues: Venue[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <svg
      viewBox="0 0 100 100"
      role="img"
      aria-labelledby="restaurant-title restaurant-desc"
      className="w-full rounded-2xl border border-slate-200 bg-[#f4f1e8] dark:border-slate-700 dark:bg-slate-900"
    >
      <title id="restaurant-title">Fictional restaurant map</title>
      <desc id="restaurant-desc">
        Synthetic venues around the fictional Echo office. Venue cards provide
        an accessible alternative.
      </desc>
      <path
        d="M0 34h100M0 73h100M38 0v100M68 0v100"
        className="stroke-white/90 dark:stroke-slate-800"
        strokeWidth="7"
      />
      <path
        d="M0 34h100M0 73h100M38 0v100M68 0v100"
        className="stroke-slate-300 dark:stroke-slate-700"
        strokeWidth="1"
        strokeDasharray="3 2"
      />
      <path
        d="M0 88c20-15 32-5 46-13s25-22 54-16v41H0z"
        className="fill-sky-200/70 dark:fill-sky-900/30"
      />
      <rect
        x="42"
        y="38"
        width="20"
        height="16"
        rx="2"
        className="fill-indigo-100 stroke-indigo-300 dark:fill-indigo-500/20 dark:stroke-indigo-500"
      />
      <text
        x="46"
        y="47"
        className="fill-indigo-700 text-[3px] font-semibold dark:fill-indigo-300"
      >
        ECHO OFFICE
      </text>
      <text x="5" y="10" className="fill-slate-400 text-[3px] font-semibold">
        MARKET SQUARE
      </text>
      <text x="72" y="10" className="fill-slate-400 text-[3px] font-semibold">
        EAST WALK
      </text>
      <text x="5" y="62" className="fill-slate-400 text-[3px] font-semibold">
        RIVERSIDE
      </text>
      <text x="71" y="62" className="fill-slate-400 text-[3px] font-semibold">
        OFFICE DISTRICT
      </text>
      {venues.map((venue) => {
        const selected = selectedId === venue.id;
        return (
          <g
            key={venue.id}
            role="button"
            tabIndex={0}
            aria-label={`${venue.name}, ${venue.cuisine}, $${venue.pricePerPerson} per person`}
            onClick={() => onSelect(venue.id)}
            onKeyDown={(event) =>
              (event.key === "Enter" || event.key === " ") && onSelect(venue.id)
            }
            className="cursor-pointer"
          >
            <circle
              cx={venue.x}
              cy={venue.y}
              r={selected ? 6 : 5}
              className={clsx(
                "stroke-2 transition",
                selected
                  ? "fill-indigo-600 stroke-white"
                  : "fill-rose-500 stroke-white hover:fill-rose-600",
              )}
            />
            <text
              x={venue.x}
              y={venue.y + 1.2}
              textAnchor="middle"
              className="pointer-events-none fill-white text-[4px] font-bold"
            >
              {selected ? "✓" : "•"}
            </text>
            <text
              x={venue.x}
              y={venue.y + 9}
              textAnchor="middle"
              className={clsx(
                "pointer-events-none text-[2.8px] font-semibold",
                selected
                  ? "fill-indigo-700 dark:fill-indigo-300"
                  : "fill-slate-600 dark:fill-slate-300",
              )}
            >
              {venue.name}
            </text>
          </g>
        );
      })}
      {!venues.length && (
        <text
          x="50"
          y="47"
          textAnchor="middle"
          className="fill-slate-500 text-[4px]"
        >
          No matching venues
        </text>
      )}
    </svg>
  );
}

export function VenueCard({
  venue,
  selected,
  onSelect,
}: {
  venue: Venue;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={clsx(
        "w-full rounded-xl border p-3 text-left transition focus-visible:outline-2 focus-visible:outline-indigo-500",
        selected
          ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500/10 dark:bg-indigo-500/10"
          : "border-slate-200 bg-white hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-1.5 font-semibold">
            <MapPin className="size-4 text-rose-500" />
            {venue.name}
          </div>
          <div className="mt-0.5 text-xs text-slate-500">
            {venue.area} · {venue.cuisine}
          </div>
        </div>
        <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
          ${venue.pricePerPerson}
          <span className="text-xs font-normal text-slate-400">/person</span>
        </span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-slate-500">
        <span className="rounded-md bg-slate-100 px-1.5 py-0.5 dark:bg-slate-800">
          Up to {venue.capacity}
        </span>
        {venue.dietary.map((item) => (
          <span
            key={item}
            className="rounded-md bg-emerald-50 px-1.5 py-0.5 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
          >
            {item}
          </span>
        ))}
        {selected && (
          <span className="ml-auto inline-flex items-center gap-1 font-medium text-indigo-600">
            <Utensils className="size-3" /> Selected
          </span>
        )}
      </div>
    </button>
  );
}
