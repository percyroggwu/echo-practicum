import clsx from "clsx";
import {
  ArrowLeft,
  ArrowRight,
  CalendarCheck,
  Check,
  MapPin,
  Sparkles,
  Utensils,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Badge, Button, inputClass } from "../components/ui";
import { ACTION_TIME_ZONE, VENUES } from "./mockActionData";
import RestaurantMap, { VenueCard } from "./RestaurantMap";
import {
  formatDate,
  formatTime,
  fromMinutes,
  isParticipantSlotFree,
  toMinutes,
} from "./schedulingUtils";
import type { EchoAction, Participant, TeamEventRecord } from "./actionTypes";

const STEPS = ["Event details", "Choose venue", "Review"];

export default function TeamEventPlanner({
  managerId,
  teamName,
  participants,
  actions,
  onSave,
  onBack,
}: {
  managerId: string;
  teamName: string;
  participants: Participant[];
  actions: EchoAction[];
  onSave: (event: Omit<TeamEventRecord, "id" | "createdAt">) => void;
  onBack: () => void;
}) {
  const [step, setStep] = useState(0);
  const [eventType, setEventType] = useState<"Lunch" | "Dinner">("Lunch");
  const [title, setTitle] = useState(`${teamName} optional team lunch`);
  const [teamSize, setTeamSize] = useState(Math.min(8, participants.length));
  const [date, setDate] = useState("2026-11-19");
  const [time, setTime] = useState("12:00");
  const [budget, setBudget] = useState(35);
  const [area, setArea] = useState("Any");
  const [dietary, setDietary] = useState("Any");
  const [requirements, setRequirements] = useState(
    "Please make participation optional and include vegetarian choices.",
  );
  const [venueId, setVenueId] = useState<string | null>(null);
  const [invitation, setInvitation] = useState(
    `You're invited to an optional ${teamName} lunch. Please join if your schedule allows—there is no expectation to attend. Reply with any dietary or accessibility needs.`,
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
      VENUES.filter(
        (venue) =>
          venue.capacity >= teamSize &&
          venue.pricePerPerson <= budget &&
          venue.eventTypes.includes(eventType) &&
          (area === "Any" || venue.area === area) &&
          (dietary === "Any" || venue.dietary.includes(dietary)),
      ),
    [teamSize, budget, eventType, area, dietary],
  );
  const venue = VENUES.find((item) => item.id === venueId) ?? null;
  const estimatedTotal = venue ? venue.pricePerPerson * teamSize : 0;
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
            Compare fictional venues and prepare an optional event plan—without
            making a reservation.
          </p>
        </div>
        <Badge tone="blue">Synthetic venues</Badge>
      </div>
      <ol className="grid grid-cols-3 gap-1">
        {STEPS.map((label, index) => (
          <li key={label}>
            <button
              type="button"
              disabled={index > step}
              onClick={() => index < step && setStep(index)}
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
              Budget per person
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
                This time overlaps a saved or synthetic calendar interval for at
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
              An optional gathering may create space for connection. It is a
              management option—not evidence that morale is low or a proven
              remedy.
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
              Area
              <select
                className="ml-2 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                value={area}
                onChange={(e) => {
                  setArea(e.target.value);
                  setVenueId(null);
                }}
              >
                <option>Any</option>
                {[...new Set(VENUES.map((item) => item.area))].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <label className="text-xs font-medium text-slate-500">
              Dietary option
              <select
                className="ml-2 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                value={dietary}
                onChange={(e) => {
                  setDietary(e.target.value);
                  setVenueId(null);
                }}
              >
                <option>Any</option>
                {[...new Set(VENUES.flatMap((item) => item.dietary))].map(
                  (value) => (
                    <option key={value}>{value}</option>
                  ),
                )}
              </select>
            </label>
            <span className="ml-auto text-xs text-slate-500">
              Budget ≤ ${budget}/person · capacity ≥ {teamSize}
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
                  No fictional venues meet all filters. Increase the budget,
                  reduce team size, or change dietary and area filters.
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
              Review the simulated plan
            </h3>
            <p className="mt-1 text-sm text-rose-50">
              No venue or calendar service is connected.
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
                label="Synthetic venue"
                value={`${venue.name} · ${venue.area}`}
              />
              <ReviewItem
                icon={Utensils}
                label="Estimated cost"
                value={`$${estimatedTotal} total (${teamSize} × $${venue.pricePerPerson}); tax, tip, and extras excluded`}
              />
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
                Requirements to confirm with the venue
              </div>
              <p className="mt-1 text-slate-600 dark:text-slate-300">
                {requirements || "None entered."}
              </p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
              <strong>Prototype status:</strong> Approval saves this plan
              locally. No restaurant reservation or real invitations will be
              made.
            </div>
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
        ) : (
          <Button
            type="button"
            variant="primary"
            icon={CalendarCheck}
            disabled={!valid[2] || !venue}
            onClick={() =>
              onSave({
                kind: "event",
                managerId,
                eventType,
                title,
                teamSize,
                participantIds,
                slot,
                budgetPerPerson: budget,
                area: venue!.area,
                requirements,
                venueId: venue!.id,
                estimatedTotal,
                invitation,
                status: "Confirmed in prototype",
                origin: {
                  kind: "synthetic-scenario",
                  label: "Synthetic team-connection scenario",
                  insightId: "team-connection",
                },
              })
            }
          >
            Approve simulated plan
          </Button>
        )}
      </div>
    </section>
  );
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
