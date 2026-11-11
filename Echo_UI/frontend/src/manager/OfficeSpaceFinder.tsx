import clsx from "clsx";
import { Building2, Check, Filter, Monitor, Users } from "lucide-react";
import { useState } from "react";
import { Badge, Button, inputClass } from "../components/ui";
import { ROOMS } from "./mockActionData";
import OfficeFloorMap from "./OfficeFloorMap";
import {
  formatDate,
  formatTime,
  fromMinutes,
  isRoomFree,
  toMinutes,
} from "./schedulingUtils";
import type { EchoAction, MeetingRoom, TimeSlot } from "./actionTypes";

export default function OfficeSpaceFinder({
  actions,
  slot: suppliedSlot,
  participantCount: suppliedCount,
  selectedRoomId,
  onChoose,
  standalone = false,
  onSaveStandalone,
}: {
  actions: EchoAction[];
  slot?: TimeSlot | null;
  participantCount?: number;
  selectedRoomId?: string | null;
  onChoose?: (room: MeetingRoom) => void;
  standalone?: boolean;
  onSaveStandalone?: (
    room: MeetingRoom,
    slot: TimeSlot,
    capacity: number,
  ) => void;
}) {
  const [date, setDate] = useState("2026-11-17");
  const [time, setTime] = useState("10:00");
  const [duration, setDuration] = useState(30);
  const [capacity, setCapacity] = useState(suppliedCount ?? 4);
  const [equipment, setEquipment] = useState("Any");
  const [floor, setFloor] = useState("Any");
  const [availableOnly, setAvailableOnly] = useState(true);
  const [selected, setSelected] = useState<string | null>(
    selectedRoomId ?? null,
  );
  const slot = suppliedSlot ?? {
    date,
    start: time,
    end: fromMinutes(toMinutes(time) + duration),
  };
  const count = suppliedCount ?? capacity;
  const compatibility = new Set(
    ROOMS.filter(
      (room) => room.capacity >= count && isRoomFree(room.id, slot, actions),
    ).map((room) => room.id),
  );
  const filtered = ROOMS.filter(
    (room) =>
      room.capacity >= count &&
      (equipment === "Any" || room.amenities.includes(equipment)) &&
      (floor === "Any" || room.floor === floor) &&
      (!availableOnly || compatibility.has(room.id)),
  );
  const filteredIds = new Set(
    filtered
      .filter((room) => compatibility.has(room.id))
      .map((room) => room.id),
  );
  const choose = (id: string) => {
    const room = ROOMS.find((item) => item.id === id);
    if (!room || !compatibility.has(id)) return;
    setSelected(id);
    onChoose?.(room);
  };
  return (
    <section className="space-y-4">
      {standalone && (
        <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-4 dark:border-slate-800 dark:bg-slate-900">
          <label className="text-xs font-medium text-slate-500">
            Date
            <input
              className={`${inputClass} mt-1`}
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
          <label className="text-xs font-medium text-slate-500">
            Start time
            <input
              className={`${inputClass} mt-1`}
              type="time"
              min="09:00"
              max="16:30"
              step="1800"
              value={time}
              onChange={(e) => setTime(e.target.value)}
            />
          </label>
          <label className="text-xs font-medium text-slate-500">
            Duration
            <select
              className={`${inputClass} mt-1`}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
            >
              {[30, 45, 60, 90].map((value) => (
                <option key={value} value={value}>
                  {value} minutes
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs font-medium text-slate-500">
            People
            <input
              className={`${inputClass} mt-1`}
              type="number"
              min={1}
              max={20}
              value={capacity}
              onChange={(e) => setCapacity(Number(e.target.value))}
            />
          </label>
        </div>
      )}
      <div className="rounded-xl border border-indigo-200 bg-indigo-50/60 px-4 py-3 text-sm text-indigo-900 dark:border-indigo-500/20 dark:bg-indigo-500/10 dark:text-indigo-200">
        <strong>{formatDate(slot.date)}</strong> · {formatTime(slot.start)}–
        {formatTime(slot.end)} · {count} {count === 1 ? "person" : "people"} ·
        synthetic office data
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,.75fr)]">
        <OfficeFloorMap
          rooms={ROOMS}
          selectedId={selected}
          availableIds={filteredIds}
          onSelect={choose}
        />
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2 rounded-xl bg-slate-100 p-2 dark:bg-slate-800/60">
            <Filter className="m-2 size-4 text-slate-400" />
            <select
              className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
              value={equipment}
              onChange={(e) => setEquipment(e.target.value)}
              aria-label="Equipment filter"
            >
              <option>Any</option>
              <option>Video</option>
              <option>Display</option>
              <option>Whiteboard</option>
              <option>Projector</option>
              <option>Accessible</option>
            </select>
            <select
              className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
              value={floor}
              onChange={(e) => setFloor(e.target.value)}
              aria-label="Floor filter"
            >
              <option>Any</option>
              {[...new Set(ROOMS.map((room) => room.floor))].map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
            <label className="flex items-center gap-1.5 px-2 text-xs">
              <input
                type="checkbox"
                checked={availableOnly}
                onChange={(e) => setAvailableOnly(e.target.checked)}
              />{" "}
              Available only
            </label>
          </div>
          <div
            className="max-h-[420px] space-y-2 overflow-y-auto pr-1"
            aria-label="Room directory"
          >
            {filtered.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700">
                No rooms match these filters for the full interval. Try a
                different time, capacity, or equipment filter.
              </div>
            )}
            {filtered.map((room) => {
              const available = compatibility.has(room.id);
              const active = selected === room.id;
              return (
                <button
                  type="button"
                  key={room.id}
                  disabled={!available}
                  onClick={() => choose(room.id)}
                  className={clsx(
                    "w-full rounded-xl border p-3 text-left transition focus-visible:outline-2 focus-visible:outline-indigo-500",
                    active
                      ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500/15 dark:bg-indigo-500/10"
                      : available
                        ? "border-slate-200 bg-white hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900"
                        : "cursor-not-allowed border-slate-200 bg-slate-50 opacity-60 dark:border-slate-800 dark:bg-slate-950",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 font-semibold">
                        <Building2 className="size-4 text-indigo-500" />
                        {room.name}
                      </div>
                      <div className="mt-0.5 text-xs text-slate-500">
                        {room.floor} · {room.type}
                      </div>
                    </div>
                    {active ? (
                      <Badge tone="blue">
                        <Check className="size-3" /> Selected
                      </Badge>
                    ) : (
                      <Badge tone={available ? "green" : "slate"}>
                        {available ? "Available" : "Unavailable"}
                      </Badge>
                    )}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Users className="size-3.5" /> {room.capacity}
                    </span>
                    {room.amenities.map((item) => (
                      <span
                        key={item}
                        className="flex items-center gap-1 rounded-md bg-slate-100 px-1.5 py-0.5 dark:bg-slate-800"
                      >
                        <Monitor className="size-3" />
                        {item}
                      </span>
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      {standalone && selected && (
        <div className="flex justify-end">
          <Button
            variant="primary"
            onClick={() => {
              const room = ROOMS.find((item) => item.id === selected);
              if (room) onSaveStandalone?.(room, slot, count);
            }}
          >
            Save simulated room plan
          </Button>
        </div>
      )}
    </section>
  );
}
