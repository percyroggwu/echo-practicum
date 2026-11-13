import {
  ArrowLeft,
  Building2,
  CalendarCheck,
  CheckCircle2,
  History,
  Sparkles,
  Utensils,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Badge, Button, Card } from "../components/ui";
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

type Tool = "overview" | "scheduler" | "rooms" | "event" | "actions";

export default function ActionCenter({
  managerId,
  teamName,
  teamSize,
  launch,
}: {
  managerId: string;
  teamName: string;
  teamSize: number;
  launch?: { token: number; prefill: SchedulerPrefill } | null;
}) {
  const participants = useMemo(
    () =>
      participantsFor(managerId, teamName).slice(
        0,
        Math.max(4, Math.min(12, teamSize)),
      ),
    [managerId, teamName, teamSize],
  );
  const [actions, setActions] = useState<EchoAction[]>(() =>
    loadActions(managerId),
  );
  const [tool, setTool] = useState<Tool>(launch ? "scheduler" : "overview");
  const [prefill, setPrefill] = useState<SchedulerPrefill | null>(
    launch?.prefill ?? null,
  );
  const [notice, setNotice] = useState("");
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
      "Meeting saved in Echo's prototype. No real calendar invitations were sent.",
    );
    setTool("actions");
  }
  function saveEvent(event: Omit<TeamEventRecord, "id" | "createdAt">) {
    const record: TeamEventRecord = {
      ...event,
      id: nextActionId(managerId, "event", actions),
      createdAt: new Date().toISOString(),
    };
    commit(
      [record, ...actions],
      "Team event saved in Echo’s prototype. No restaurant reservation or real invitations were made.",
    );
    setTool("actions");
  }
  function open(toolName: Tool, nextPrefill: SchedulerPrefill | null = null) {
    setNotice("");
    setPrefill(nextPrefill);
    setTool(toolName);
  }
  function updateStatus(id: string, status: ActionStatus) {
    const action = actions.find((item) => item.id === id);
    if (!action) return;
    if (action.status === "Cancelled" && status === "Planned") {
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
          "This action cannot be restored at its old time because a participant or room now has a conflicting prototype booking.",
        );
        return;
      }
    }
    commit(
      actions.map((item) => (item.id === id ? { ...item, status } : item)),
      status === "Cancelled"
        ? "Action cancelled. Its participant and room time is available again in the prototype."
        : undefined,
    );
  }
  if (tool === "scheduler")
    return (
      <MeetingScheduler
        managerId={managerId}
        participants={participants}
        actions={actions}
        prefill={prefill}
        onSave={saveMeeting}
        onBack={() => open("overview")}
      />
    );
  if (tool === "event")
    return (
      <TeamEventPlanner
        managerId={managerId}
        teamName={teamName}
        participants={participants}
        actions={actions}
        onSave={saveEvent}
        onBack={() => open("overview")}
      />
    );
  if (tool === "rooms")
    return (
      <section className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <button
              type="button"
              onClick={() => open("overview")}
              className="mb-2 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"
            >
              <ArrowLeft className="size-4" /> Action Center
            </button>
            <h2 className="text-2xl font-semibold">Office Space Finder</h2>
            <p className="mt-1 text-sm text-slate-500">
              Explore a fictional office and save a simulated room plan.
            </p>
          </div>
          <Badge tone="blue">Synthetic floor plan</Badge>
        </div>
        <OfficeSpaceFinder
          standalone
          actions={actions}
          onSaveStandalone={(room, slot) =>
            saveMeeting({
              kind: "meeting",
              managerId,
              title: `Office space plan · ${room.name}`,
              purpose: "General team meeting",
              description:
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
                "Confirm participants and meeting purpose before using this plan.",
              status: "Planned",
              origin: {
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
              <History className="size-6 text-indigo-500" /> My Actions
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Manager-scoped prototype records stored separately from official
              HR data.
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
      title: "Schedule Meeting",
      description:
        "Find shared availability, choose a room, and edit an agenda.",
      icon: CalendarCheck,
      tone: "from-indigo-500 to-violet-600",
    },
    {
      id: "rooms" as const,
      title: "Find Office Space",
      description:
        "Filter available rooms on a responsive fictional floor plan.",
      icon: Building2,
      tone: "from-cyan-500 to-blue-600",
    },
    {
      id: "event" as const,
      title: "Plan Team Event",
      description:
        "Compare synthetic venues, costs, and accessibility options.",
      icon: Utensils,
      tone: "from-rose-500 to-orange-500",
    },
  ];
  return (
    <section className="space-y-8">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-violet-900 p-6 text-white shadow-xl sm:p-8">
        <div className="absolute -right-20 -top-24 size-72 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="relative max-w-2xl">
          <Badge
            className="bg-white/10 text-indigo-100 ring-white/20"
            tone="blue"
          >
            <Sparkles className="size-3" /> Manager-approved action
          </Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Echo Action Center
          </h1>
          <p className="mt-3 text-base leading-7 text-indigo-100">
            Turn a reviewed insight into a practical next step. Explore the
            evidence, choose a simulated tool, approve the plan, and track what
            happened—all while keeping the manager in control.
          </p>
          <div className="mt-5 flex flex-wrap gap-2 text-xs text-indigo-200">
            <span>Identify</span>
            <span>→</span>
            <span>Explain</span>
            <span>→</span>
            <span>Recommend</span>
            <span>→</span>
            <span>Approve</span>
            <span>→</span>
            <span>Track</span>
          </div>
        </div>
      </div>

      <section>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Recommended for your team</h2>
            <p className="mt-1 text-sm text-slate-500">
              Curated examples distinguish evidence, uncertainty, and suggested
              interventions.
            </p>
          </div>
          <span className="text-xs text-slate-500">Human review required</span>
        </div>
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

      <section>
        <h2 className="text-xl font-semibold">Available action tools</h2>
        <p className="mt-1 text-sm text-slate-500">
          All interactions remain inside this frontend prototype.
        </p>
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
            <h2 className="text-xl font-semibold">My Actions</h2>
            <p className="mt-1 text-sm text-slate-500">
              Saved locally for {managerId}; no official records are changed.
            </p>
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
