import {
  ArrowLeft,
  Building2,
  CalendarCheck,
  CheckCircle2,
  History,
  Utensils,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button, Card } from "../components/ui";
import ActionHistory from "./ActionHistory";
import ActionRecommendationCard from "./ActionRecommendationCard";
import { loadActions, nextActionId, saveActions } from "./actionStore";
import type {
  ActionStatus,
  EchoAction,
  MeetingRecord,
  SchedulerPrefill,
  TeamEventRecord,
} from "./actionTypes";
import MeetingScheduler from "./MeetingScheduler";
import { participantsFor, RECOMMENDATIONS } from "./mockActionData";
import OfficeSpaceFinder from "./OfficeSpaceFinder";
import { isParticipantSlotFree, isRoomFree } from "./schedulingUtils";
import TeamEventPlanner from "./TeamEventPlanner";
import AnswerPlanSection, { planParticipants, type ProposedMeeting } from "./AnswerPlanSection";
import { demoRef } from "./booking";
import type { AnswerPlan } from "./visual";
import type { EventPrefill, RoomPrefill } from "./AnswerPlanSection";

type Tool = "overview" | "scheduler" | "rooms" | "event" | "actions";

export default function ActionCenter({
  managerId,
  teamName,
  teamSize,
  launch,
  plan,
}: {
  managerId: string;
  teamName: string;
  teamSize: number;
  launch?: { token: number; prefill: SchedulerPrefill } | null;
  /** When opened from an answer: the actions Echo suggested for it, shown first. */
  plan?: AnswerPlan | null;
}) {
  const participants = useMemo(
    () => [
      ...(plan ? planParticipants(plan, managerId, teamName) : []),
      ...participantsFor(managerId, teamName).slice(
        0,
        Math.max(4, Math.min(12, teamSize)),
      ),
    ],
    [managerId, teamName, teamSize, plan],
  );
  const [actions, setActions] = useState<EchoAction[]>(() =>
    loadActions(managerId),
  );
  const [tool, setTool] = useState<Tool>(launch ? "scheduler" : "overview");
  const [prefill, setPrefill] = useState<SchedulerPrefill | null>(
    launch?.prefill ?? null,
  );
  const [notice, setNotice] = useState("");
  // Filled in when an answer's action opens the event planner or the room finder.
  const [eventPrefill, setEventPrefill] = useState<EventPrefill | null>(null);
  const [roomPrefill, setRoomPrefill] = useState<RoomPrefill | null>(null);
  // Each tool opens at its top, not wherever the page was scrolled to.
  const top = useRef<HTMLSpanElement>(null);
  const opened = useRef(false);
  useEffect(() => {
    // On first open the page starts at the very top (with the answer picker above); later tool changes scroll here.
    if (!opened.current) {
      opened.current = true;
      document.getElementById("echo-main")?.scrollTo({ top: 0 });
      return;
    }
    top.current?.scrollIntoView({ block: "start" });
  }, [tool]);
  function commit(next: EchoAction[], message?: string) {
    setActions(next);
    saveActions(managerId, next);
    if (message) setNotice(message);
  }
  function saveMeeting(meeting: Omit<MeetingRecord, "id" | "createdAt">) {
    const record: MeetingRecord = {
      ...meeting,
      id: nextActionId(managerId, "meeting", actions),
      createdAt: new Date().toISOString(),
    };
    commit(
      [record, ...actions],
      meeting.bookingRef
        ? `Booked. Reference ${meeting.bookingRef}. You'll find it in My actions.`
        : "Meeting scheduled. You'll find it in My actions.",
    );
    setTool(plan ? "overview" : "actions");
  }
  /** Saves every meeting Echo lined up, once the manager agreed to the whole set. */
  function saveAll(meetings: ProposedMeeting[]) {
    let next = actions;
    for (const { person: _person, ...meeting } of meetings)
      next = [{ ...meeting, ...(meeting.location.type === "room" ? { bookingRef: demoRef("RM") } : {}), id: nextActionId(managerId, "meeting", next), createdAt: new Date().toISOString() }, ...next];
    commit(
      next,
      `${meetings.length} meeting${meetings.length === 1 ? "" : "s"} booked, rooms reserved. You'll find them in My actions.`,
    );
  }
  function saveEvent(event: Omit<TeamEventRecord, "id" | "createdAt">) {
    const record: TeamEventRecord = {
      ...event,
      id: nextActionId(managerId, "event", actions),
      createdAt: new Date().toISOString(),
    };
    commit(
      [record, ...actions],
      event.bookingRef
        ? `Table booked. Reference ${event.bookingRef}.`
        : "Team lunch plan saved.",
    );
    setTool(plan ? "overview" : "actions");
  }
  function open(toolName: Tool, nextPrefill: SchedulerPrefill | null = null) {
    setNotice("");
    setPrefill(nextPrefill);
    setEventPrefill(null);
    setRoomPrefill(null);
    setTool(toolName);
  }
  function updateStatus(id: string, status: ActionStatus) {
    const action = actions.find((item) => item.id === id);
    if (!action) return;
    // Restoring or rebooking a cancelled action must not clash with what was booked since.
    if (action.status === "Cancelled" && status !== "Cancelled" && status !== "Completed") {
      const participantsFree = isParticipantSlotFree(
        action.participantIds,
        action.slot,
        actions,
        action.id,
      );
      const roomFree =
        action.kind !== "meeting" ||
        action.location.type !== "room" ||
        !action.location.roomId ||
        isRoomFree(action.location.roomId, action.slot, actions, action.id);
      if (!participantsFree || !roomFree) {
        setNotice(
          "This can't be rebooked at its old time: a participant or the room is now taken.",
        );
        return;
      }
    }
    commit(
      actions.map((item) => (item.id === id ? { ...item, status } : item)),
      status === "Cancelled"
        ? "Cancelled. The room and everyone's time are free again."
        : undefined,
    );
  }
  if (tool === "scheduler")
    return (
      <>
      <span ref={top} />
      <MeetingScheduler
        managerId={managerId}
        participants={participants}
        actions={actions}
        prefill={prefill}
        onSave={saveMeeting}
        onBack={() => open("overview")}
      />
      </>
    );
  if (tool === "event")
    return (
      <>
      <span ref={top} />
      <TeamEventPlanner
        managerId={managerId}
        teamName={teamName}
        participants={participants}
        actions={actions}
        onSave={saveEvent}
        onBack={() => open("overview")}
        prefill={eventPrefill}
      />
      </>
    );
  if (tool === "rooms")
    return (
      <section className="space-y-5">
        <span ref={top} />
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <button
              type="button"
              onClick={() => open("overview")}
              className="mb-2 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"
            >
              <ArrowLeft className="size-4" /> Action Center
            </button>
            <h2 className="text-2xl font-semibold">Find a room</h2>
            <p className="mt-1 text-sm text-slate-500">
              {roomPrefill
                ? `Pick a room for: ${roomPrefill.title}`
                : "See which rooms are free right now."}
            </p>
          </div>
          
        </div>
        <OfficeSpaceFinder
          standalone
          actions={actions}
          onSaveStandalone={(room, slot) =>
            saveMeeting({
              kind: "meeting",
              managerId,
              title: roomPrefill
                ? `${roomPrefill.title} · ${room.name}`
                : `Office space plan · ${room.name}`,
              purpose: roomPrefill ? "Team engagement" : "General team meeting",
              description:
                roomPrefill?.description ??
                "Independent room-selection preview created in Action Center.",
              participantIds: [],
              slot,
              duration:
                Number(slot.end.slice(0, 2)) * 60 +
                Number(slot.end.slice(3)) -
                (Number(slot.start.slice(0, 2)) * 60 +
                  Number(slot.start.slice(3))),
              location: { type: "room", roomId: room.id, label: room.name },
              agenda:
                roomPrefill?.agenda ??
                "Confirm participants and meeting purpose before using this plan.",
              status: "Planned",
              origin: roomPrefill?.origin ?? {
                kind: "manager-created",
                label: "Created in Office Space Finder",
              },
            })
          }
        />
      </section>
    );
  if (tool === "actions")
    return (
      <section className="space-y-5">
        <span ref={top} />
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <button
              type="button"
              onClick={() => open("overview")}
              className="mb-2 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"
            >
              <ArrowLeft className="size-4" /> Action Center
            </button>
            <h2 className="flex items-center gap-2 text-2xl font-semibold">
              <History className="size-6 text-indigo-500" /> My actions
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Saved in this browser only. No HR records change.
            </p>
          </div>
          <Button
            variant="primary"
            icon={CalendarCheck}
            onClick={() => open("scheduler")}
          >
            New meeting
          </Button>
        </div>
        {notice && (
          <div
            className="flex gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200"
            role="status"
          >
            <CheckCircle2 className="size-5 shrink-0" />
            {notice}
          </div>
        )}
        <ActionHistory actions={actions} onStatus={updateStatus} />
      </section>
    );

  const tools = [
    {
      id: "scheduler" as const,
      title: "Schedule a meeting",
      description: "Find a time, a room and an agenda.",
      icon: CalendarCheck,
      tone: "from-indigo-500 to-violet-600",
    },
    {
      id: "rooms" as const,
      title: "Find a room",
      description: "See which rooms are free on the floor plan.",
      icon: Building2,
      tone: "from-cyan-500 to-blue-600",
    },
    {
      id: "event" as const,
      title: "Plan a team lunch",
      description: "Restaurants near the office, with tables to book.",
      icon: Utensils,
      tone: "from-rose-500 to-orange-500",
    },
  ];
  return (
    <section className="space-y-8">
      <span ref={top} />
      {plan && notice && (
        <div
          className="flex gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200"
          role="status"
        >
          <CheckCircle2 className="size-5 shrink-0" />
          {notice}
        </div>
      )}
      {plan ? (
        <AnswerPlanSection
          plan={plan}
          managerId={managerId}
          actions={actions}
          onSchedule={(next) => open("scheduler", next)}
          onEvent={(next) => {
            open("event");
            setEventPrefill(next);
          }}
          onRoom={(next) => {
            open("rooms");
            setRoomPrefill(next);
          }}
          onConfirmAll={saveAll}
        />
      ) : (
      <div className="ask-hero relative overflow-hidden rounded-3xl px-6 py-7 text-white sm:px-8">
        <div className="relative">
          <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            Action Center
          </h1>
          <p className="mt-2 text-[15px] text-[#dfe6cf]">
            Turn what Echo found into a next step. Nothing happens without your approval.
          </p>
        </div>
      </div>
      )}

      {!plan && (
      <section>
        <h2 className="text-xl font-semibold">Suggested for your team</h2>
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          {RECOMMENDATIONS.map((item, index) => (
            <ActionRecommendationCard
              key={item.id}
              recommendation={item}
              onOpen={() =>
                item.tool === "event"
                  ? open("event")
                  : open("scheduler", {
                      title: item.title,
                      purpose:
                        index === 0
                          ? "Recognition discussion"
                          : "Workload check-in",
                      description: `${item.context} ${item.limitation}`,
                      participantIds: [
                        participants[index]?.id ?? participants[0].id,
                      ],
                      origin: {
                        kind: "existing-evidence",
                        label: item.category,
                        insightId: item.id,
                      },
                    })
              }
            />
          ))}
        </div>
      </section>
      )}

      <section>
        <h2 className="text-xl font-semibold">Tools</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {tools.map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={() => open(item.id)}
              className="group overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-1 hover:shadow-lg focus-visible:outline-2 focus-visible:outline-indigo-500 dark:border-slate-800 dark:bg-slate-900"
            >
              <div className={`bg-gradient-to-br ${item.tone} p-5 text-white`}>
                <item.icon className="size-7" />
                <h3 className="mt-6 text-lg font-semibold">{item.title}</h3>
              </div>
              <p className="p-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {item.description}
              </p>
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">My actions</h2>
            <p className="mt-1 text-sm text-slate-500">Saved in this browser only.</p>
          </div>
          {actions.length > 3 && (
            <Button variant="ghost" onClick={() => open("actions")}>
              View all
            </Button>
          )}
        </div>
        <Card className="mt-4 p-4">
          <ActionHistory
            actions={actions.slice(0, 3)}
            onStatus={updateStatus}
          />
        </Card>
      </section>
    </section>
  );
}
