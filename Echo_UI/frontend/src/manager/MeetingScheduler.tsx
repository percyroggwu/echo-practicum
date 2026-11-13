import clsx from "clsx";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CalendarCheck,
  Check,
  Clock,
  FileText,
  Monitor,
  Plus,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Badge, Button, inputClass } from "../components/ui";
import { ACTION_TIME_ZONE, ROOMS } from "./mockActionData";
import OfficeSpaceFinder from "./OfficeSpaceFinder";
import {
  addDays,
  formatDate,
  formatTime,
  suggestedSlots,
  weekDates,
} from "./schedulingUtils";
import type {
  EchoAction,
  MeetingPurpose,
  MeetingRecord,
  Participant,
  SchedulerPrefill,
  TimeSlot,
} from "./actionTypes";
import WeeklyCalendar from "./WeeklyCalendar";

const PURPOSES: MeetingPurpose[] = [
  "Recognition discussion",
  "Workload check-in",
  "Cross-team coordination",
  "Team engagement",
  "General team meeting",
];
/** The agenda as a numbered list: one editable line per item, with add and remove. Stored as "1. …\n2. …". */
function AgendaList({ agenda, onChange }: { agenda: string; onChange: (next: string) => void }) {
  const items = agenda.split("\n").map((line) => line.replace(/^\s*\d+\.\s?/, ""));
  const save = (next: string[]) => onChange(next.map((item, i) => `${i + 1}. ${item}`).join("\n"));
  return (
    <div className="mt-4 space-y-2">
      {items.map((item, i) => (
        <div key={i} className="group flex items-start gap-2.5">
          <span className="mt-2 grid size-6 shrink-0 place-items-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-800 dark:bg-indigo-500/20 dark:text-indigo-200">
            {i + 1}
          </span>
          <textarea
            value={item}
            rows={Math.max(1, Math.ceil(item.length / 48))}
            onChange={(e) => save(items.map((value, j) => (j === i ? e.target.value.replace(/\n/g, " ") : value)))}
            aria-label={`Agenda item ${i + 1}`}
            className="min-w-0 flex-1 resize-none rounded-lg border border-transparent bg-slate-50 px-3 py-2 text-sm leading-6 outline-none transition hover:border-slate-200 focus:border-indigo-400 focus:bg-white dark:bg-slate-800/60 dark:hover:border-slate-700 dark:focus:bg-slate-950"
          />
          <button
            type="button"
            onClick={() => save(items.filter((_, j) => j !== i))}
            aria-label={`Remove agenda item ${i + 1}`}
            className="mt-2 grid size-6 shrink-0 place-items-center rounded-md text-slate-400 opacity-0 transition hover:bg-rose-50 hover:text-rose-600 focus-visible:opacity-100 group-hover:opacity-100 dark:hover:bg-rose-500/10"
          >
            <X className="size-3.5" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => save([...items, ""])}
        className="ml-8 inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 dark:text-indigo-300 dark:hover:bg-indigo-500/10"
      >
        <Plus className="size-3.5" /> Add item
      </button>
    </div>
  );
}

/** The reason for the meeting, from its description: the first sentence or two, without the "From Echo's answer" line. */
function reasonFrom(description: string) {
  const text = description.split(/\n\s*\nFrom Echo's answer/)[0].replace(/\s+/g, " ").trim();
  const sentences = text.match(/[^.!?]+[.!?]?/g) ?? [];
  let reason = "";
  for (const sentence of sentences) {
    if (reason && (reason + sentence).length > 170) break;
    reason += sentence;
  }
  // Read as the manager's words: drop Echo's tags, lower-case the opening, and turn self-review "my" into "their".
  return reason
    .replace(/\s*In no goal, no record\.?/i, "")
    .trim()
    .replace(/[.!?]$/, "")
    .replace(/^Helped ([^:]+): (.)/, (_, team: string, c: string) => `helping ${team}, where ${c.toLowerCase()}`)
    .replace(/^(.)/, (c) => c.toLowerCase())
    .replace(/\bmy\b/g, "their")
    .replace(/\bI\b/g, "they");
}

/** A short agenda written for this meeting: its purpose, the reason it was set up, and who it is with. */
function agendaFor(purpose: MeetingPurpose, title: string, description: string, person?: string) {
  const why = reasonFrom(description);
  const who = person ?? "them";
  const lines: Record<MeetingPurpose, string[]> = {
    "Recognition discussion": [
      why ? `Thank ${who} for ${why.startsWith("helping") ? why : `the work: ${why}`}` : `Thank ${who} for the work, naming what it achieved`,
      "Ask what it took, and who else helped",
      "Agree how to recognize it: a note, a mention to the team, or in their review",
      "Decide whether this kind of work belongs in next year's goals",
    ],
    "Workload check-in": [
      why ? `Why we're talking: ${why}` : `Go through what ${who === "them" ? "they have" : `${who} has`} on right now`,
      "Which requests from other teams take the most time?",
      "Agree one thing to drop, delay or hand off",
      "Pick a date to check in again",
    ],
    "Cross-team coordination": [
      `Why we're meeting: ${why || title}`,
      "What each team needs from the other",
      "How requests and feedback reach the right manager from now on",
      "Agree owners and dates",
    ],
    "Team engagement": [
      `Why we're meeting: ${why || title}`,
      "Open floor: what's working, and what's getting in the way",
      "Agree one change to try",
      "Pick when we'll check whether it helped",
    ],
    "General team meeting": [`Purpose: ${why || title}`, "Updates", "Decisions needed", "Owners and next steps"],
  };
  return lines[purpose].map((line, i) => `${i + 1}. ${line}.`).join("\n");
}
const STEPS = ["Details", "Availability", "Location", "Agenda", "Confirm"];

export default function MeetingScheduler({
  managerId,
  participants,
  actions,
  prefill,
  onSave,
  onBack,
}: {
  managerId: string;
  participants: Participant[];
  actions: EchoAction[];
  prefill?: SchedulerPrefill | null;
  onSave: (meeting: Omit<MeetingRecord, "id" | "createdAt">) => void;
  onBack: () => void;
}) {
  const initialPurpose = prefill?.purpose ?? "Recognition discussion";
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState(prefill?.title ?? "Recognition follow-up");
  const [purpose, setPurpose] = useState<MeetingPurpose>(initialPurpose);
  const [description, setDescription] = useState(prefill?.description ?? "");
  const [participantIds, setParticipantIds] = useState<string[]>(
    prefill?.participantIds?.length
      ? prefill.participantIds
      : participants.slice(0, 2).map((person) => person.id),
  );
  const [duration, setDuration] = useState(30);
  const [week, setWeek] = useState("2026-11-16");
  const [slot, setSlot] = useState<TimeSlot | null>(null);
  const [locationType, setLocationType] = useState<"room" | "virtual" | "none">(
    "room",
  );
  const [roomId, setRoomId] = useState<string | null>(null);
  const dates = useMemo(() => weekDates(week), [week]);
  const suggestions = useMemo(
    () => suggestedSlots(participantIds, dates, duration, actions),
    [participantIds, dates, duration, actions],
  );
  const selectedPeople = participants.filter((person) =>
    participantIds.includes(person.id),
  );
  const selectedRoom = ROOMS.find((room) => room.id === roomId);
  // The agenda follows the details until the manager edits it; after that it is theirs.
  const draftAgenda = (p: MeetingPurpose) =>
    agendaFor(p, title, description, selectedPeople.length === 1 || p === "Recognition discussion" ? selectedPeople[0]?.name.split(" ")[0] : undefined);
  const [agenda, setAgenda] = useState(() => draftAgenda(initialPurpose));
  const [agendaEdited, setAgendaEdited] = useState(false);
  useEffect(() => {
    if (step === 3 && !agendaEdited) setAgenda(draftAgenda(purpose));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  function changePurpose(next: MeetingPurpose) {
    setPurpose(next);
    setAgenda(draftAgenda(next));
    setAgendaEdited(false);
    if (!title.trim() || PURPOSES.some((value) => title === value))
      setTitle(next);
  }
  const valid = [
    title.trim() && participantIds.length > 0,
    !!slot,
    locationType !== "room" || !!roomId,
    agenda.trim(),
    true,
  ];
  const location =
    locationType === "room"
      ? {
          type: "room" as const,
          roomId: roomId!,
          label: selectedRoom?.name ?? "Room",
        }
      : locationType === "virtual"
        ? {
            type: "virtual" as const,
            label: "Echo virtual meeting (simulated)",
          }
        : { type: "none" as const, label: "No room needed" };
  const next = () => valid[step] && setStep((value) => Math.min(value + 1, 4));

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
            Smart Meeting Scheduler
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Plan with deterministic synthetic calendars. Nothing is sent to a
            real calendar.
          </p>
        </div>
        <Badge tone="blue">Frontend prototype</Badge>
      </div>
      <ol className="grid grid-cols-5 gap-1" aria-label="Scheduling steps">
        {STEPS.map((label, index) => (
          <li key={label}>
            <button
              type="button"
              onClick={() => index < step && setStep(index)}
              disabled={index > step}
              className={clsx(
                "flex w-full flex-col items-center gap-1 rounded-xl px-1 py-2 text-center text-[10px] font-semibold uppercase tracking-wide sm:text-xs",
                index === step
                  ? "bg-indigo-600 text-white"
                  : index < step
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300"
                    : "bg-slate-100 text-slate-400 dark:bg-slate-800",
              )}
            >
              <span className="grid size-5 place-items-center rounded-full bg-current/10">
                {index < step ? <Check className="size-3" /> : index + 1}
              </span>
              {label}
            </button>
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
          <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <label className="block text-sm font-medium">
              Meeting title
              <input
                className={`${inputClass} mt-1.5`}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label className="block text-sm font-medium">
              Purpose
              <select
                className={`${inputClass} mt-1.5`}
                value={purpose}
                onChange={(e) =>
                  changePurpose(e.target.value as MeetingPurpose)
                }
              >
                {PURPOSES.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-medium">
              Duration
              <select
                className={`${inputClass} mt-1.5`}
                value={duration}
                onChange={(e) => {
                  setDuration(Number(e.target.value));
                  setSlot(null);
                  setRoomId(null);
                }}
              >
                {[15, 30, 45, 60].map((value) => (
                  <option key={value} value={value}>
                    {value} minutes
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-medium">
              Description{" "}
              <span className="font-normal text-slate-400">(optional)</span>
              <textarea
                className={`${inputClass} mt-1.5 min-h-24`}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Context the participants should have before the conversation"
              />
            </label>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h3 className="font-semibold">Participants</h3>
                <p className="text-xs text-slate-500">
                  Synthetic directory for {managerId}; anonymous survey
                  respondents are never shown.
                </p>
              </div>
              <Badge>{participantIds.length} selected</Badge>
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {participants.map((person) => (
                <label
                  key={person.id}
                  className={clsx(
                    "flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition",
                    participantIds.includes(person.id)
                      ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-500/10"
                      : "border-slate-200 hover:border-indigo-300 dark:border-slate-700",
                  )}
                >
                  <input
                    type="checkbox"
                    checked={participantIds.includes(person.id)}
                    onChange={() => {
                      setParticipantIds((ids) =>
                        ids.includes(person.id)
                          ? ids.filter((id) => id !== person.id)
                          : [...ids, person.id],
                      );
                      setSlot(null);
                      setRoomId(null);
                    }}
                  />
                  <span className="grid size-8 shrink-0 place-items-center rounded-full bg-slate-200 text-xs font-semibold dark:bg-slate-700">
                    {person.initials}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">
                      {person.name}
                    </span>
                    <span className="block truncate text-xs text-slate-500">
                      {person.role}
                    </span>
                  </span>
                </label>
              ))}
            </div>
            {!participantIds.length && (
              <p className="mt-3 text-sm text-rose-600" role="alert">
                Select at least one participant.
              </p>
            )}
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <WeeklyCalendar
            week={week}
            dates={dates}
            participants={participants}
            participantIds={participantIds}
            duration={duration}
            actions={actions}
            selected={slot}
            onSelect={setSlot}
            onPrevious={() => {
              setWeek(addDays(week, -7));
              setSlot(null);
            }}
            onNext={() => {
              setWeek(addDays(week, 7));
              setSlot(null);
            }}
          />
          <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h3 className="font-semibold">Suggested common times</h3>
            <p className="mt-0.5 text-xs text-slate-500">
              These use the same duration and availability logic as the
              calendar.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestions.length ? (
                suggestions.map((item) => (
                  <button
                    type="button"
                    key={`${item.date}-${item.start}`}
                    onClick={() => setSlot(item)}
                    className={clsx(
                      "rounded-xl border px-3 py-2 text-left text-sm transition",
                      slot?.date === item.date && slot.start === item.start
                        ? "border-indigo-500 bg-indigo-600 text-white"
                        : "border-slate-200 hover:border-indigo-300 dark:border-slate-700",
                    )}
                  >
                    <span className="block font-medium">
                      {formatDate(item.date)}
                    </span>
                    <span className="text-xs opacity-75">
                      {formatTime(item.start)}–{formatTime(item.end)}
                    </span>
                  </button>
                ))
              ) : (
                <p className="text-sm text-slate-500">
                  No common availability this week. Navigate to another week or
                  adjust participants and duration.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {step === 2 && slot && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            {(
              [
                {
                  id: "room",
                  label: "Company room",
                  icon: Building2,
                  note: "Choose from the synthetic floor plan",
                },
                {
                  id: "virtual",
                  label: "Virtual meeting",
                  icon: Monitor,
                  note: "Simulated Echo meeting link",
                },
                {
                  id: "none",
                  label: "No room",
                  icon: Users,
                  note: "Walking meeting or other arrangement",
                },
              ] as const
            ).map((option) => (
              <button
                type="button"
                key={option.id}
                onClick={() => {
                  setLocationType(option.id);
                  if (option.id !== "room") setRoomId(null);
                }}
                className={clsx(
                  "rounded-2xl border p-4 text-left transition",
                  locationType === option.id
                    ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500/10 dark:bg-indigo-500/10"
                    : "border-slate-200 bg-white hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900",
                )}
              >
                <option.icon className="size-5 text-indigo-500" />
                <div className="mt-2 font-semibold">{option.label}</div>
                <div className="text-xs text-slate-500">{option.note}</div>
              </button>
            ))}
          </div>
          {locationType === "room" && (
            <OfficeSpaceFinder
              actions={actions}
              slot={slot}
              participantCount={participantIds.length}
              selectedRoomId={roomId}
              onChoose={(room) => setRoomId(room.id)}
            />
          )}
        </div>
      )}

      {step === 3 && (
        <div className="grid gap-5 lg:grid-cols-[1fr_.8fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2">
              <FileText className="size-5 text-indigo-500" />
              <h3 className="font-semibold">Agenda</h3>
              {agendaEdited && (
                <button
                  type="button"
                  onClick={() => {
                    setAgenda(draftAgenda(purpose));
                    setAgendaEdited(false);
                  }}
                  className="ml-auto text-xs text-slate-500 hover:text-indigo-600"
                >
                  Reset
                </button>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Written from this meeting's details. Change anything.
            </p>
            <AgendaList
              agenda={agenda}
              onChange={(next) => {
                setAgenda(next);
                setAgendaEdited(true);
              }}
            />
          </div>
          <Summary
            title={title}
            purpose={purpose}
            people={selectedPeople}
            duration={duration}
            slot={slot}
            location={location.label}
            description={description}
          />
        </div>
      )}

      {step === 4 && (
        <div className="mx-auto max-w-3xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="bg-gradient-to-r from-indigo-600 to-violet-600 p-6 text-white">
            <CalendarCheck className="size-8" />
            <h3 className="mt-3 text-2xl font-semibold">
              Ready for manager approval
            </h3>
            <p className="mt-1 text-sm text-indigo-100">
              Review the full plan before saving it to this browser.
            </p>
          </div>
          <div className="p-6">
            <Summary
              title={title}
              purpose={purpose}
              people={selectedPeople}
              duration={duration}
              slot={slot}
              location={location.label}
              description={description}
            />
            <div className="mt-5 rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Agenda
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6">
                {agenda}
              </p>
            </div>
            <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
              <strong>Simulated invitation status:</strong> Ready to save in
              Echo. No calendar provider is connected.
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
        <Button
          type="button"
          variant="ghost"
          icon={ArrowLeft}
          onClick={() => (step ? setStep(step - 1) : onBack())}
        >
          {step ? "Back" : "Cancel"}
        </Button>
        {step < 4 ? (
          <Button
            type="button"
            variant="primary"
            icon={ArrowRight}
            disabled={!valid[step]}
            onClick={next}
          >
            Continue
          </Button>
        ) : (
          <Button
            type="button"
            variant="primary"
            icon={CalendarCheck}
            onClick={() =>
              onSave({
                kind: "meeting",
                managerId,
                title,
                purpose,
                description,
                participantIds,
                slot: slot!,
                duration,
                location,
                agenda,
                status: "Confirmed in prototype",
                origin: prefill?.origin ?? {
                  kind: "manager-created",
                  label: "Created in Action Center",
                },
              })
            }
          >
            Approve and save meeting
          </Button>
        )}
      </div>
    </section>
  );
}

function Summary({
  title,
  purpose,
  people,
  duration,
  slot,
  location,
  description,
}: {
  title: string;
  purpose: MeetingPurpose;
  people: Participant[];
  duration: number;
  slot: TimeSlot | null;
  location: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-slate-500">{purpose}</p>
      <dl className="mt-4 space-y-3 text-sm">
        <div className="flex gap-3">
          <Users className="mt-0.5 size-4 shrink-0 text-indigo-500" />
          <div>
            <dt className="text-xs text-slate-500">Participants</dt>
            <dd>{people.map((person) => person.name).join(", ")}</dd>
          </div>
        </div>
        <div className="flex gap-3">
          <Clock className="mt-0.5 size-4 shrink-0 text-indigo-500" />
          <div>
            <dt className="text-xs text-slate-500">Time</dt>
            <dd>
              {slot
                ? `${formatDate(slot.date)} · ${formatTime(slot.start)}–${formatTime(slot.end)} · ${ACTION_TIME_ZONE.replace("_", " ")}`
                : "Not selected"}{" "}
              ({duration} min)
            </dd>
          </div>
        </div>
        <div className="flex gap-3">
          <Building2 className="mt-0.5 size-4 shrink-0 text-indigo-500" />
          <div>
            <dt className="text-xs text-slate-500">Location</dt>
            <dd>{location}</dd>
          </div>
        </div>
        {description && (
          <div>
            <dt className="text-xs text-slate-500">Description</dt>
            <dd>{description}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}
