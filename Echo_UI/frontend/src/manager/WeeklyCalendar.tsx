import clsx from "clsx";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { ACTION_TIME_ZONE } from "./mockActionData";
import {
  formatDate,
  formatTime,
  fromMinutes,
  isParticipantSlotFree,
  participantBusy,
  toMinutes,
  WORK_END,
  WORK_START,
} from "./schedulingUtils";
import type { EchoAction, Participant, TimeSlot } from "./actionTypes";

export default function WeeklyCalendar({
  week,
  dates,
  participants,
  participantIds,
  duration,
  actions,
  selected,
  onSelect,
  onPrevious,
  onNext,
}: {
  week: string;
  dates: string[];
  participants: Participant[];
  participantIds: string[];
  duration: number;
  actions: EchoAction[];
  selected: TimeSlot | null;
  onSelect: (slot: TimeSlot) => void;
  onPrevious: () => void;
  onNext: () => void;
}) {
  const rows = Array.from(
    { length: (WORK_END - WORK_START) / 30 },
    (_, index) => WORK_START + index * 30,
  );
  const selectedPeople = participants.filter((person) =>
    participantIds.includes(person.id),
  );
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 font-semibold">
            <CalendarDays className="size-4 text-indigo-500" /> Week of{" "}
            {formatDate(week, { month: "long", day: "numeric" })}
          </div>
          <div className="mt-0.5 text-xs text-slate-500">
            {ACTION_TIME_ZONE.replace("_", " ")} · 30-minute grid · synthetic
            availability
          </div>
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onPrevious}
            className="rounded-lg border border-slate-200 p-2 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
            aria-label="Previous week"
          >
            <ChevronLeft className="size-4" />
          </button>
          <button
            type="button"
            onClick={onNext}
            className="rounded-lg border border-slate-200 p-2 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
            aria-label="Next week"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <div className="min-w-[720px]">
          <div className="grid grid-cols-[72px_repeat(5,minmax(110px,1fr))] border-b border-slate-200 dark:border-slate-800">
            <div />
            {dates.map((date) => (
              <div
                key={date}
                className="border-l border-slate-100 px-2 py-2 text-center dark:border-slate-800"
              >
                <div className="text-xs font-semibold">
                  {formatDate(date, { weekday: "short" })}
                </div>
                <div className="text-[11px] text-slate-500">
                  {formatDate(date, { month: "short", day: "numeric" })}
                </div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-[72px_repeat(5,minmax(110px,1fr))]">
            <div>
              {rows.map((minute) => (
                <div
                  key={minute}
                  className="h-9 border-b border-slate-100 pr-2 pt-1 text-right text-[10px] text-slate-400 dark:border-slate-800/70"
                >
                  {minute % 60 === 0 ? formatTime(fromMinutes(minute)) : ""}
                </div>
              ))}
            </div>
            {dates.map((date) => (
              <div
                key={date}
                className="border-l border-slate-100 dark:border-slate-800"
              >
                {rows.map((minute) => {
                  const slot = {
                    date,
                    start: fromMinutes(minute),
                    end: fromMinutes(minute + duration),
                  };
                  const inBounds = minute + duration <= WORK_END;
                  const free =
                    inBounds &&
                    participantIds.length > 0 &&
                    isParticipantSlotFree(participantIds, slot, actions);
                  const conflictNames = selectedPeople
                    .filter((person) =>
                      participantBusy(person.id, actions).some(
                        (busy) =>
                          busy.date === date &&
                          toMinutes(busy.start) < minute + duration &&
                          minute < toMinutes(busy.end),
                      ),
                    )
                    .map((person) => person.name.split(" ")[0]);
                  const active =
                    selected?.date === date && selected.start === slot.start;
                  return (
                    <button
                      type="button"
                      key={minute}
                      disabled={!free}
                      onClick={() => onSelect(slot)}
                      title={
                        free
                          ? `Available ${formatTime(slot.start)}–${formatTime(slot.end)}`
                          : conflictNames.length
                            ? `Busy: ${conflictNames.join(", ")}`
                            : participantIds.length
                              ? "Meeting would extend past work hours"
                              : "Select participants first"
                      }
                      aria-label={`${formatDate(date)} ${formatTime(slot.start)} ${free ? "available" : "unavailable"}`}
                      className={clsx(
                        "h-9 w-full border-b border-slate-100 px-1 text-left text-[10px] transition focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-indigo-500 dark:border-slate-800/70",
                        active && "bg-indigo-600 text-white",
                        !active &&
                          free &&
                          "bg-emerald-50/60 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-500/5 dark:text-emerald-300 dark:hover:bg-emerald-500/15",
                        !active &&
                          !free &&
                          "cursor-not-allowed bg-slate-100/70 text-slate-400 dark:bg-slate-950/50",
                      )}
                    >
                      {active
                        ? `${formatTime(slot.start)} selected`
                        : !free && conflictNames.length
                          ? conflictNames.join(", ")
                          : free
                            ? "Available"
                            : ""}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
