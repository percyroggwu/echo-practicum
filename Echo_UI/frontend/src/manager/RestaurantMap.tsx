import clsx from "clsx";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { ExternalLink, MapPin, Utensils } from "lucide-react";
import { useEffect, useRef } from "react";
import type { Venue } from "./actionTypes";
import { OFFICE, VENUES_CHECKED } from "./venues";

const escape = (text: string) => text.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

/** A pin with a name tag, drawn as HTML so it matches the rest of the app. */
function pin(name: string, selected: boolean, office = false) {
  const dot = office
    ? '<span class="grid size-7 shrink-0 place-items-center rounded-lg bg-slate-800 text-white shadow-md ring-2 ring-white"><svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/></svg></span>'
    : `<span class="grid size-7 shrink-0 place-items-center rounded-full text-white shadow-md ring-2 ring-white ${selected ? "bg-indigo-600 scale-110" : "bg-rose-500"}"><svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2M7 2v20M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg></span>`;
  // Close pins would overlap, so only the office and the selected venue carry a name tag; the rest show it on hover.
  if (!selected && !office)
    return L.divIcon({ className: "", html: `<span class="flex" style="transform:translate(0,-50%)">${dot}</span>`, iconSize: [0, 0], iconAnchor: [14, 0] });
  const tag = `<span class="whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold shadow-sm ring-1 ${
    selected ? "bg-indigo-600 text-white ring-indigo-600" : office ? "bg-slate-800 text-white ring-slate-800" : "bg-white text-slate-700 ring-slate-200"
  }">${escape(name)}</span>`;
  return L.divIcon({ className: "", html: `<span class="flex items-center gap-1.5" style="transform:translate(0,-50%)">${dot}${tag}</span>`, iconSize: [0, 0], iconAnchor: [14, 0] });
}

/** A real map (OpenStreetMap) of the venues near the office. Clicking a pin selects the venue; nothing is booked. */
export default function RestaurantMap({
  venues,
  selectedId,
  onSelect,
}: {
  venues: Venue[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);
  const select = useRef(onSelect);
  select.current = onSelect;

  useEffect(() => {
    if (!box.current || map.current) return;
    map.current = L.map(box.current, { scrollWheelZoom: false, zoomControl: true, fadeAnimation: false }).setView([OFFICE.lat, OFFICE.lon], 16);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    if (!map.current || !layer.current) return;
    layer.current.clearLayers();
    L.marker([OFFICE.lat, OFFICE.lon], { icon: pin(OFFICE.name, false, true), keyboard: false, title: OFFICE.note, zIndexOffset: 2000 }).addTo(layer.current);
    for (const venue of venues) {
      const selected = venue.id === selectedId;
      const marker = L.marker([venue.lat, venue.lon], { icon: pin(venue.name, selected), zIndexOffset: selected ? 1000 : 0, alt: venue.name })
        .on("click", () => select.current(venue.id))
        .addTo(layer.current);
      if (!selected) marker.bindTooltip(venue.name, { direction: "top", offset: [0, -18] });
    }
    const points = [[OFFICE.lat, OFFICE.lon], ...venues.map((v) => [v.lat, v.lon])] as [number, number][];
    if (selectedId) return;
    // Leaflet measures its box when it starts; the box can still be settling, so measure again before fitting.
    const fit = () => {
      map.current?.invalidateSize();
      map.current?.fitBounds(L.latLngBounds(points), { padding: [36, 36], maxZoom: 17 });
    };
    fit();
    const timer = window.setTimeout(fit, 250);
    return () => window.clearTimeout(timer);
  }, [venues, selectedId]);

  return (
    <div>
      <div ref={box} className="relative z-0 aspect-square w-full overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700" aria-label="Map of real restaurants near the office. The list beside it offers the same choices." />
      <p className="mt-1.5 text-[11px] text-slate-500">
        Real places, checked {VENUES_CHECKED}. {OFFICE.note}. Echo doesn't book or contact any restaurant.
      </p>
    </div>
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
    <div
      className={clsx(
        "rounded-xl border p-3 transition",
        selected
          ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500/10 dark:bg-indigo-500/10"
          : "border-slate-200 bg-white hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900",
      )}
    >
      <button type="button" onClick={onSelect} className="block w-full text-left focus-visible:outline-2 focus-visible:outline-indigo-500">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 font-semibold">
              <MapPin className="size-4 shrink-0 text-rose-500" />
              {venue.name}
            </div>
            <div className="mt-0.5 text-xs text-slate-500">{venue.address}</div>
          </div>
          {selected && (
            <span className="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-indigo-600">
              <Utensils className="size-3" /> Selected
            </span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-slate-600 dark:text-slate-300">
          <span className="rounded-md bg-slate-100 px-1.5 py-0.5 dark:bg-slate-800">{venue.walk} min walk</span>
          <span className="rounded-md bg-slate-100 px-1.5 py-0.5 dark:bg-slate-800">{venue.cuisine}</span>
          {venue.meals?.map((meal) => (
            <span key={meal} className="rounded-md bg-emerald-50 px-1.5 py-0.5 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              {meal}
            </span>
          ))}
        </div>
        {venue.note && <p className="mt-2 text-xs leading-5 text-slate-500">{venue.note}</p>}
      </button>
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
        <a href={venue.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium text-indigo-700 hover:underline dark:text-indigo-300">
          Menu and hours <ExternalLink className="size-3" />
        </a>
        <span className="text-slate-400">
          Source:{" "}
          <a href={venue.source.url} target="_blank" rel="noreferrer" className="hover:underline">
            {venue.source.label}
          </a>
        </span>
      </div>
    </div>
  );
}
