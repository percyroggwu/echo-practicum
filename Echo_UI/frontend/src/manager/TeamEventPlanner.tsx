import clsx from "clsx";
import {
  ArrowLeft,
  ArrowRight,
  CalendarCheck,
  Check,
  CircleCheckBig,
  Copy,
  ExternalLink,
  MapPin,
  Sparkles,
  Utensils,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Button, inputClass } from "../components/ui";
import { ACTION_TIME_ZONE, VENUES } from "./mockActionData";
import RestaurantMap, { VenueCard } from "./RestaurantMap";
import {
  formatDate,
  formatTime,
  fromMinutes,
  isParticipantSlotFree,
  toMinutes,
} from "./schedulingUtils";
import type { ActionOrigin, EchoAction, Participant, TeamEventRecord } from "./actionTypes";
import { BookingSteps, demoRef, simulatedTables, useBookingSequence } from "./booking";

const STEPS = ["Event details", "Choose venue", "Review", "Booked"];

const SEATING = ["Indoor table", "Private or semi-private area", "Outdoor, if weather allows"] as const;
// Kinds of food for the filter: the first word of each cuisine, e.g. "American" from "American, made from scratch".
const CUISINES = [...new Set(VENUES.map((v) => v.cuisine.split(",")[0].trim()))].filter((c) => c !== "Restaurant").sort();

export default function TeamEventPlanner({
  managerId,
  teamName,
  participants,
  actions,
  onSave,
  onBack,
  prefill,
}: {
  /** From an answer's action: the event's title, invitation and where it came from. */
  prefill?: { title?: string; invitation?: string; origin?: ActionOrigin } | null;
  managerId: string;
  teamName: string;
  participants: Participant[];
  actions: EchoAction[];
  onSave: (event: Omit<TeamEventRecord, "id" | "createdAt">) => void;
  onBack: () => void;
}) {
  const [step, setStep] = useState(0);
  const [eventType, setEventType] = useState<"Lunch" | "Dinner">("Lunch");
  const [title, setTitle] = useState(prefill?.title ?? `${teamName} optional team lunch`);
  const [teamSize, setTeamSize] = useState(Math.min(8, participants.length));
  const [date, setDate] = useState("2026-11-19");
  const [time, setTime] = useState("12:00");
  const [budget, setBudget] = useState(35);
  const [maxWalk, setMaxWalk] = useState(10);
  const [food, setFood] = useState("Any");
  const [requirements, setRequirements] = useState(
    "Optional to attend. Check the menu for vegetarian and other dietary needs, and step-free access.",
  );
  const [venueId, setVenueId] = useState<string | null>(null);
  // Set once the manager books the table in the demo; the restaurant itself is never contacted.
  const [bookingRef, setBookingRef] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [seating, setSeating] = useState<(typeof SEATING)[number]>(SEATING[0]);
  const [requests, setRequests] = useState("Some guests may be vegetarian; please note any step-free access.");
  const [invitation, setInvitation] = useState(
    prefill?.invitation ?? `You're invited to an optional ${teamName} lunch. Please join if your schedule allows—there is no expectation to attend. Reply with any dietary or accessibility needs.`,
  );
  const duration = eventType === "Lunch" ? 90 : 120;
  const slot = {
    date,
    start: time,
    end: fromMinutes(toMinutes(time) + duration),
  };
  const participantIds = participants
    .slice(0, teamSize)
    .map((person) => person.id);
  const calendarFree = isParticipantSlotFree(participantIds, slot, actions);
  const venues = useMemo(
    () =>
      // Every checked place is shown; lunch/dinner is a tag on the card where a source gave it, not a filter.
      VENUES.filter(
        (venue) =>
          venue.walk <= maxWalk &&
          (food === "Any" || venue.cuisine.includes(food)),
      ),
    [maxWalk, food],
  );
  const venue = VENUES.find((item) => item.id === venueId) ?? null;
  const tableSteps = venue
    ? [`Checking tables for ${teamSize} at ${venue.name}, ${formatDate(date)} ${formatTime(time)}`, `Holding a table: ${seating.toLowerCase()}`, "Confirming the reservation"]
    : [];
  const tableBooking = useBookingSequence(tableSteps, 700);
  // The manager's own spending limit, not a quote: Echo has no menu prices for real restaurants.
  const estimatedTotal = budget * teamSize;
  const valid = [
    title.trim() && teamSize > 0 && calendarFree,
    !!venue && venues.some((item) => item.id === venue.id),
    invitation.trim(),
  ];
  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={onBack}
            className="mb-2 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"
          >
            <ArrowLeft className="size-4" /> Action Center
          </button>
          <h2 className="text-2xl font-semibold tracking-tight">
            Team Dinner & Event Planner
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Restaurants near the office. Pick a place, book a table, and invite the team.
          </p>
        </div>
        
      </div>
      <ol className="grid grid-cols-4 gap-1">
        {STEPS.map((label, index) => (
          <li key={label}>
            <button
              type="button"
              disabled={index > step}
              onClick={() => index < step && step < 3 && setStep(index)}
              className={clsx(
                "flex w-full items-center justify-center gap-2 rounded-xl px-2 py-2 text-xs font-semibold",
                step === index
                  ? "bg-indigo-600 text-white"
                  : index < step
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300"
                    : "bg-slate-100 text-slate-400 dark:bg-slate-800",
              )}
            >
              {index < step ? <Check className="size-3.5" /> : index + 1}{" "}
              {label}
            </button>
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div className="grid gap-5 lg:grid-cols-[1fr_.8fr]">
          <div className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-2 dark:border-slate-800 dark:bg-slate-900">
            <div className="sm:col-span-2">
              <span className="text-sm font-medium">Event type</span>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {(["Lunch", "Dinner"] as const).map((value) => (
                  <button
                    type="button"
                    key={value}
                    onClick={() => {
                      setEventType(value);
                      setTitle(
                        `${teamName} optional team ${value.toLowerCase()}`,
                      );
                      setVenueId(null);
                      setTime(value === "Lunch" ? "12:00" : "18:00");
                    }}
                    className={clsx(
                      "rounded-xl border p-3 text-sm font-semibold",
                      eventType === value
                        ? "border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300"
                        : "border-slate-200 dark:border-slate-700",
                    )}
                  >
                    <Utensils className="mx-auto mb-1 size-5" />
                    {value}
                  </button>
                ))}
              </div>
            </div>
            <label className="text-sm font-medium sm:col-span-2">
              Event title
              <input
                className={`${inputClass} mt-1.5`}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label className="text-sm font-medium">
              Team size
              <input
                className={`${inputClass} mt-1.5`}
                type="number"
                min={2}
                max={participants.length}
                value={teamSize}
                onChange={(e) => {
                  setTeamSize(Number(e.target.value));
                  setVenueId(null);
                }}
              />
            </label>
            <label className="text-sm font-medium">
              Your budget per person
              <input
                className={`${inputClass} mt-1.5`}
                type="number"
                min={15}
                max={100}
                value={budget}
                onChange={(e) => {
                  setBudget(Number(e.target.value));
                  setVenueId(null);
                }}
              />
            </label>
            <label className="text-sm font-medium">
              Preferred date
              <input
                className={`${inputClass} mt-1.5`}
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </label>
            <label className="text-sm font-medium">
              Time
              <input
                className={`${inputClass} mt-1.5`}
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </label>
            <label className="text-sm font-medium sm:col-span-2">
              Dietary and accessibility notes
              <textarea
                className={`${inputClass} mt-1.5 min-h-24`}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
              />
            </label>
            {!calendarFree && (
              <p
                className="sm:col-span-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200"
                role="alert"
              >
                This time overlaps an existing calendar entry for at
                least one demo participant. Choose another time before
                continuing.
              </p>
            )}
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-700 p-6 text-white">
            <Sparkles className="size-7" />
            <h3 className="mt-5 text-xl font-semibold">
              Suggested intervention
            </h3>
            <p className="mt-2 text-sm leading-6 text-indigo-100">
              Optional and nice to have, not a fix for morale.
            </p>
            <div className="mt-5 rounded-xl bg-white/10 p-4 text-sm">
              <strong>Human review:</strong> Check budget, workload,
              accessibility, and whether employees actually want this format.
              Attendance must remain voluntary.
            </div>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <label className="text-xs font-medium text-slate-500">
              Walk from the office
              <select
                className="ml-2 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                value={maxWalk}
                onChange={(e) => setMaxWalk(Number(e.target.value))}
              >
                {[5, 10, 15].map((minutes) => (
                  <option key={minutes} value={minutes}>
                    Up to {minutes} min
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs font-medium text-slate-500">
              Food
              <select
                className="ml-2 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                value={food}
                onChange={(e) => setFood(e.target.value)}
              >
                <option>Any</option>
                {CUISINES.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <span className="ml-auto self-center text-xs text-slate-500">
              {venues.length} places · {teamSize} people · your budget ${budget}/person. Check prices, hours and group size with the restaurant.
            </span>
          </div>
          <div className="grid gap-4 lg:grid-cols-[1.15fr_.85fr]">
            <RestaurantMap
              venues={venues}
              selectedId={venueId}
              onSelect={setVenueId}
            />
            <div className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
              {venues.length ? (
                venues.map((item) => (
                  <VenueCard
                    key={item.id}
                    venue={item}
                    selected={venueId === item.id}
                    onSelect={() => setVenueId(item.id)}
                  />
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 dark:border-slate-700">
                  No checked restaurants match. Allow a longer walk or another kind of food.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {step === 2 && venue && (
        <div className="mx-auto max-w-3xl overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="bg-gradient-to-r from-rose-500 to-orange-500 p-6 text-white">
            <Utensils className="size-8" />
            <h3 className="mt-3 text-2xl font-semibold">
              Review your plan
            </h3>
            <p className="mt-1 text-sm text-rose-50">
              Check the details, then book the table.
            </p>
          </div>
          <div className="space-y-5 p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <ReviewItem
                icon={Users}
                label="Event"
                value={`${title} · ${teamSize} people`}
              />
              <ReviewItem
                icon={CalendarCheck}
                label="Date and time"
                value={`${formatDate(date)} · ${formatTime(time)} · ${ACTION_TIME_ZONE.replace("_", " ")}`}
              />
              <ReviewItem
                icon={MapPin}
                label="Restaurant"
                value={`${venue.name} · ${venue.address}`}
              />
              <ReviewItem
                icon={Utensils}
                label="Budget"
                value={`Up to $${estimatedTotal} (${teamSize} × $${budget}). Your limit, not a quote from the restaurant.`}
              />
            </div>
            <div className="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div className="font-semibold">Reservation</div>
                <div className="text-xs text-slate-500">Available times for {formatDate(date)}</div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label="Table time">
                {simulatedTables(venue.id, date, time).map((t) => (
                  <button
                    key={t.time}
                    type="button"
                    role="radio"
                    aria-checked={t.time === time}
                    disabled={!t.open}
                    onClick={() => setTime(t.time)}
                    className={clsx(
                      "rounded-lg border px-3 py-1.5 text-sm font-medium tabular-nums transition",
                      t.time === time
                        ? "border-indigo-600 bg-indigo-600 text-white"
                        : t.open
                          ? "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
                          : "cursor-not-allowed border-slate-100 text-slate-300 line-through dark:border-slate-800 dark:text-slate-600",
                    )}
                  >
                    {formatTime(t.time)}
                  </button>
                ))}
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <label className="block text-sm font-medium">
                  Seating
                  <select className={`${inputClass} mt-1.5`} value={seating} onChange={(e) => setSeating(e.target.value as (typeof SEATING)[number])}>
                    {SEATING.map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </label>
                <div className="text-sm">
                  <div className="font-medium">Reservation under</div>
                  <div className="mt-1.5 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/60">{teamName} · party of {teamSize}</div>
                </div>
              </div>
              <label className="mt-3 block text-sm font-medium">
                Special requests
                <textarea className={`${inputClass} mt-1.5 min-h-16`} value={requests} onChange={(e) => setRequests(e.target.value)} />
              </label>
            </div>
            <label className="block text-sm font-medium">
              Invitation message
              <textarea
                className={`${inputClass} mt-1.5 min-h-32`}
                value={invitation}
                onChange={(e) => setInvitation(e.target.value)}
              />
            </label>
            <div className="rounded-xl bg-slate-50 p-4 text-sm dark:bg-slate-800/60">
              <div className="font-medium">
                To check with the restaurant yourself
              </div>
              <p className="mt-1 text-slate-600 dark:text-slate-300">
                {requirements || "None entered."}
              </p>
            </div>
          </div>
        </div>
      )}

      {step === 3 && venue && bookingRef && !tableBooking.finished && (
        <div className="mx-auto max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-lg font-semibold">Booking your table</h3>
          <BookingSteps steps={tableSteps} done={tableBooking.done} />
        </div>
      )}

      {step === 3 && venue && bookingRef && tableBooking.finished && (
        <div className="mx-auto max-w-2xl overflow-hidden rounded-2xl border border-emerald-200 bg-white shadow-sm dark:border-emerald-500/30 dark:bg-slate-900">
          <div className="flex items-center gap-4 bg-emerald-50 p-6 dark:bg-emerald-500/10">
            <CircleCheckBig className="size-12 shrink-0 text-emerald-600 dark:text-emerald-400" />
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">Table booked</div>
              <h3 className="mt-0.5 text-2xl font-semibold tracking-tight">{venue.name}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-300">{venue.address}</p>
            </div>
          </div>
          <div className="space-y-5 p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <ReviewItem icon={CalendarCheck} label="When" value={`${formatDate(date)} · ${formatTime(time)}`} />
              <ReviewItem icon={Users} label="Party" value={`${teamSize} people · under ${teamName}`} />
              <ReviewItem icon={Utensils} label="Budget" value={`Up to $${estimatedTotal} (your limit)`} />
              <ReviewItem icon={Check} label="Reference" value={bookingRef} />
              <ReviewItem icon={MapPin} label="Seating" value={seating} />
              <ReviewItem icon={Sparkles} label="Requests" value={requests.trim() || "None"} />
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
              <div className="flex items-center gap-2 text-sm font-medium">
                Invitation for the team
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard?.writeText(invitation).catch(() => undefined);
                    setCopied(true);
                  }}
                  className="ml-auto inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900"
                >
                  {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />} {copied ? "Copied" : "Copy"}
                </button>
              </div>
              <p className="mt-1.5 whitespace-pre-line text-sm text-slate-600 dark:text-slate-300">{invitation}</p>
            </div>
            <a href={venue.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-700 hover:underline dark:text-indigo-300">
              {venue.name}: menu and hours <ExternalLink className="size-3.5" />
            </a>
          </div>
        </div>
      )}

      <div className="flex justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
        <Button
          type="button"
          variant="ghost"
          icon={ArrowLeft}
          onClick={() => (step ? setStep(step - 1) : onBack())}
        >
          {step ? "Back" : "Cancel"}
        </Button>
        {step < 2 ? (
          <Button
            type="button"
            variant="primary"
            icon={ArrowRight}
            disabled={!valid[step]}
            onClick={() => setStep(step + 1)}
          >
            Continue
          </Button>
        ) : step === 2 ? (
          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="ghost" disabled={!valid[2] || !venue} onClick={() => save(null)}>
              Just save the plan
            </Button>
            <Button
              type="button"
              variant="primary"
              icon={Utensils}
              disabled={!valid[2] || !venue}
              onClick={() => {
                setBookingRef((ref) => ref ?? demoRef("TB"));
                setStep(3);
                tableBooking.start();
              }}
            >
              Book table
            </Button>
          </div>
        ) : (
          <Button type="button" variant="primary" icon={Check} disabled={!tableBooking.finished} onClick={() => save(bookingRef)}>
            Done
          </Button>
        )}
      </div>
    </section>
  );

  function save(ref: string | null) {
    if (!venue) return;
    onSave({
                kind: "event",
                managerId,
                eventType,
                title,
                teamSize,
                participantIds,
                slot,
                budgetPerPerson: budget,
                area: `${venue.walk} min walk`,
                requirements: [requirements, ref ? `Seating: ${seating}. Requests: ${requests.trim() || "none"}.` : ""].filter(Boolean).join(" "),
                venueId: venue.id,
                estimatedTotal,
                invitation,
                ...(ref ? { bookingRef: ref } : {}),
                status: ref ? "Confirmed in prototype" : "Planned",
                origin: prefill?.origin ?? {
                  kind: "synthetic-scenario",
                  label: "Team lunch",
                  insightId: "team-connection",
                },
    });
  }
}

function ReviewItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: string;
}) {
  return (
    <div className="flex gap-3">
      <Icon className="mt-0.5 size-5 shrink-0 text-indigo-500" />
      <div>
        <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </div>
        <div className="mt-1 text-sm">{value}</div>
      </div>
    </div>
  );
}
