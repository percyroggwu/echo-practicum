import { Check, Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

/** A reference number shaped like a real booking's, marked as Echo's demo (e.g. ECHO-RM-7K2Q). */
export function demoRef(prefix: string) {
  return `ECHO-${prefix}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
}

/**
 * Plays a booking system's short "working on it" sequence: each step spins, then ticks.
 * Nothing is contacted; it only paces the confirmation so it reads like a real booking.
 */
export function useBookingSequence(steps: string[], stepMs = 650) {
  const [done, setDone] = useState(-1); // index of the last finished step; -1 = not started
  const [running, setRunning] = useState(false);
  const timer = useRef<number | null>(null);
  useEffect(() => () => { if (timer.current) window.clearTimeout(timer.current); }, []);
  function start() {
    setRunning(true);
    setDone(-1);
    let i = 0;
    const tick = () => {
      setDone(i);
      i += 1;
      if (i < steps.length) timer.current = window.setTimeout(tick, stepMs);
      else setRunning(false);
    };
    timer.current = window.setTimeout(tick, stepMs);
  }
  return { start, running, finished: done >= steps.length - 1, done };
}

/** The visible list for useBookingSequence. */
export function BookingSteps({ steps, done }: { steps: string[]; done: number }) {
  return (
    <ul className="space-y-2.5 py-2" aria-live="polite">
      {steps.map((label, i) => {
        const state = i <= done ? "done" : i === done + 1 ? "active" : "waiting";
        return (
          <li key={label} className={`flex items-center gap-3 text-sm ${state === "waiting" ? "text-slate-400" : ""}`}>
            <span
              className={`grid size-6 shrink-0 place-items-center rounded-full ${
                state === "done" ? "bg-emerald-500 text-white" : state === "active" ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/15" : "bg-slate-100 dark:bg-slate-800"
              }`}
            >
              {state === "done" ? <Check className="size-3.5" /> : state === "active" ? <Loader2 className="size-3.5 animate-spin" /> : null}
            </span>
            {label}
          </li>
        );
      })}
    </ul>
  );
}

/** Minutes before/after a "HH:MM" time, as "HH:MM". */
export function shiftTime(time: string, minutes: number) {
  const [h, m] = time.split(":").map(Number);
  const total = h * 60 + m + minutes;
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

/** Repeatable "availability" for a restaurant on a day: the same venue and date always show the same open times. */
export function simulatedTables(venueId: string, date: string, around: string) {
  const seed = [...`${venueId}${date}`].reduce((s, c) => (s * 31 + c.charCodeAt(0)) >>> 0, 7);
  return [-45, -30, -15, 0, 15, 30, 45].map((offset, i) => ({
    time: shiftTime(around, offset),
    // About a third of the times show as taken, never the one the manager asked for.
    open: offset === 0 || ((seed >> (i * 3)) & 7) > 2,
  }));
}
